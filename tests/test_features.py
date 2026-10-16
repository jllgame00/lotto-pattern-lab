import numpy as np
import pandas as pd
import pytest

from src.analysis.features import build_features, feature_columns


def extend(history, n=180):
    frame = pd.concat([history] * (n // len(history) + 1), ignore_index=True).iloc[:n].copy()
    frame['draw_no'] = np.arange(1, n + 1)
    frame['draw_date'] = pd.date_range('2002-12-07', periods=n, freq='7D')
    return frame


def test_alignment_bonus_and_current(history):
    frame = build_features(extend(history, 110), include_current=True)
    assert len(frame) == 7 * 45
    row = frame.query('target_draw == 105 and number == 1').iloc[0]
    assert row.feature_cutoff == 104
    assert row.appeared_next == 0  # fixture draw 9
    assert frame.query('number == 45 and target_draw <= 110').appeared_next.sum() == 0
    assert frame.query('target_draw == 111').appeared_next.isna().all()
    assert frame.groupby('target_draw').size().eq(45).all()


def test_prefix_invariance_and_target_poison(history):
    data = extend(history)
    all_rows = build_features(data, include_current=True)
    prefix = build_features(data.iloc[:160], include_current=True)
    columns = ['target_draw', 'number', *feature_columns('full')]
    columns = list(dict.fromkeys(columns))
    pd.testing.assert_frame_equal(all_rows.query('target_draw <= 161')[columns].reset_index(drop=True),
                                  prefix[columns].reset_index(drop=True))
    changed = data.copy()
    changed.loc[160:, [f'num{i}' for i in range(1, 7)]] = [20,21,22,23,24,25]
    poison = build_features(changed)
    pd.testing.assert_frame_equal(all_rows.query('target_draw == 161')[columns].reset_index(drop=True),
                                  poison.query('target_draw == 161')[columns].reset_index(drop=True))


def test_frequency_gap_and_groups(history):
    frame = build_features(extend(history, 110))
    row = frame.query('target_draw == 105 and number == 1').iloc[0]
    assert row.current_gap == 0  # draw104 is fixture draw8
    assert row.count_5 == 2  # draws100 and104
    assert row.rate_5 == .4
    assert row.consecutive == 0
    assert set(feature_columns('frequency_gap')) == set(feature_columns('frequency') + feature_columns('gap'))
    assert not set(feature_columns('calendar')) & set(feature_columns('periodicity'))
    assert 'appeared_next' not in feature_columns('full')
    with pytest.raises(ValueError): feature_columns('nonsense')
    with pytest.raises(ValueError): build_features(history, min_history=5)


def test_regime_confirmation_is_not_backdated(history,monkeypatch):
    import src.analysis.features as module
    calls=0
    def metrics(values):
        nonlocal calls
        index=calls%76
        calls+=1
        score=.9 if 52<=index<56 else .1
        return dict(periodicity_score=score,dominant_lag=7,acf_strength=.2,
                    dominant_period=7.,spectral_strength=.2)
    monkeypatch.setattr(module,'periodicity_metrics',metrics)
    frame=build_features(extend(history,180)).query('number == 17').set_index('target_draw')
    assert frame.loc[157:158,'strong_regime'].eq(0).all()
    assert frame.loc[159,'strong_regime']==1 and frame.loc[159,'regime_age']==0
    assert frame.loc[160,'regime_age']==1
    assert frame.loc[161,'strong_regime']==0 and frame.loc[161,'since_strong_regime']==1
