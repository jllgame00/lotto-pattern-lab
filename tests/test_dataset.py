import pandas as pd
import pytest

from src.collect.dataset import DatasetError, merge_history, validate_history, missing_draws


def test_sort_and_calendar_fields(history):
    result = validate_history(history.iloc[::-1])
    assert result.draw_no.tolist() == list(range(1, 13))
    assert result.iloc[0].year == 2002
    assert result.iloc[0].month == 12
    assert result.iloc[0].iso_week == 49
    assert result.iloc[0].weekday == 5


@pytest.mark.parametrize('column,value', [
    ('num2', 1), ('num1', 0), ('num1', 46), ('num1', 1.5),
    ('num1', True), ('bonus', 1), ('bonus', 46), ('bonus', 1.5),
    ('draw_no', 0), ('draw_no', 1.5), ('draw_date', 'not-a-date'),
    ('draw_date', '2002-12-08'), ('num1', None),
])
def test_invalid_rows_rejected(history, column, value):
    history[column] = history[column].astype(object)
    history.loc[0, column] = value
    with pytest.raises(DatasetError):
        validate_history(history)


def test_missing_and_duplicate_draws_rejected(history):
    with pytest.raises(DatasetError, match='duplicate'):
        validate_history(pd.concat([history, history.iloc[:1]]))
    with pytest.raises(DatasetError, match='Missing'):
        validate_history(history.drop(index=3))
    assert missing_draws(history.drop(index=3), end=14) == [4, 13, 14]
    with pytest.raises(DatasetError, match='Missing'):
        validate_history(history.iloc[1:])


def test_merge_is_idempotent_and_rejects_conflicts(history):
    result = merge_history(history.iloc[:6], history.iloc[3:])
    assert len(result) == 12
    assert len(merge_history(result, history)) == 12
    conflict = history.iloc[:1].copy()
    conflict.loc[0, 'bonus'] = 44
    with pytest.raises(DatasetError, match='Conflicting'):
        merge_history(history, conflict)


def test_empty_missing_columns_and_extra_features(history):
    with pytest.raises(DatasetError):
        validate_history(history.iloc[:0])
    with pytest.raises(DatasetError):
        validate_history(history.drop(columns='bonus'))
    history['future_feature'] = 123
    assert 'future_feature' not in validate_history(history)


def test_merge_does_not_drop_null_draw_numbers_or_missing_columns(history):
    invalid = history.iloc[:1].copy()
    invalid['draw_no'] = None
    with pytest.raises(DatasetError):
        merge_history(history, pd.concat([history, invalid]))
    with pytest.raises(DatasetError):
        merge_history(history, history.drop(columns='draw_no'))
