from dataclasses import asdict

import pandas as pd
import pytest

from src.backtest.engine import run_backtest
from src.backtest.metrics import random_expectation, summarize
from src.collect.dataset import DatasetError, RAW_COLUMNS
from src.models.random_model import RandomModel


def test_random_tickets_are_legal_and_seeded(history):
    model = RandomModel()
    for seed in range(50):
        ticket = model.predict(history, seed=seed)
        assert len(set(ticket)) == 6
        assert all(type(n) is int and 1 <= n <= 45 for n in ticket)
        assert ticket == model.predict(history, seed=seed)
    assert set(model.score_numbers(history)) == set(range(1,46))
    assert set(model.score_numbers(history).values()) == {6/45}
    for k in (0,5,7,46,True,6.0):
        with pytest.raises(ValueError): model.predict(history, k=k)


def test_walk_forward_only_supplies_prior_canonical_rows(history):
    seen = []
    class SpyModel:
        def predict(self, train, context=None, k=6, seed=None):
            assert train.draw_no.tolist() == list(range(1, context.draw_no))
            assert set(train.columns) == set(RAW_COLUMNS)
            assert set(asdict(context)) == {'draw_no', 'draw_date'}
            assert context.draw_date == train.iloc[-1].draw_date + pd.Timedelta(days=7)
            seen.append(context.draw_no)
            return [1,2,3,4,5,6]
    history['future_feature'] = 999
    result = run_backtest(history, SpyModel, min_train=3)
    assert seen == list(range(4,13))
    assert result.target_draw.tolist() == seen
    assert result.train_end.tolist() == list(range(3,12))
    assert result.matches.tolist() == [6,0,0,0,6,0,0,0,0]


def test_future_and_target_perturbations_cannot_change_prediction(history):
    class HistoryModel:
        def predict(self, train, context=None, k=6, seed=None):
            offset = int(train.num1.sum()) % 39
            return list(range(offset+1, offset+7))
    before = run_backtest(history, HistoryModel, min_train=3, start=5, end=5)
    changed = history.copy()
    changed.loc[changed.draw_no >= 5, [f'num{i}' for i in range(1,7)]] = [20,21,22,23,24,25]
    after = run_backtest(changed, HistoryModel, min_train=3, start=5, end=5)
    assert before.iloc[0].prediction == after.iloc[0].prediction
    assert before.iloc[0].matches != after.iloc[0].matches


def test_model_cannot_mutate_source_or_retain_state_between_tickets(history):
    original = history.copy(deep=True)
    class MutatingModel:
        def __init__(self): self.calls = 0
        def predict(self, train, context=None, k=6, seed=None):
            self.calls += 1
            assert self.calls == 1
            assert train.iloc[0].num1 == 1
            train.loc[:, 'num1'] = 40
            return [1,2,3,4,5,6]
    run_backtest(history, MutatingModel, min_train=3, tickets=2, repeats=2)
    pd.testing.assert_frame_equal(history, original)


def test_random_checkpoints_seeds_and_ticket_streams(history):
    kwargs = dict(mode='checkpoints', min_train=3, checkpoints=5, tickets=3, repeats=2, seed=77)
    a = run_backtest(history, RandomModel, **kwargs)
    b = run_backtest(history, RandomModel, **kwargs)
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 30 and a.target_draw.nunique() == 5
    assert len(a.ticket_seed.unique()) == 30
    one = run_backtest(history, RandomModel, min_train=3, start=int(a.target_draw.min()),
                       end=int(a.target_draw.min()), seed=77)
    assert one.iloc[0].prediction == a.iloc[0].prediction


@pytest.mark.parametrize('kwargs', [dict(min_train=0), dict(min_train=12), dict(tickets=0),
    dict(repeats=0), dict(seed=-1), dict(start=3,min_train=3), dict(end=13),
    dict(mode='bad'), dict(mode='checkpoints',checkpoints=100)])
def test_invalid_configuration(history, kwargs):
    options = dict(min_train=3)
    options.update(kwargs)
    with pytest.raises(ValueError): run_backtest(history, RandomModel, **options)


def test_missing_draws_and_illegal_model_tickets_are_rejected(history):
    with pytest.raises(DatasetError):
        run_backtest(history.drop(index=3), RandomModel, min_train=3)
    class BadModel:
        def predict(self, *args, **kwargs): return [1,1,2,3,4,5]
    with pytest.raises(ValueError): run_backtest(history, BadModel, min_train=3)


def test_metrics_against_hand_computed_results(history):
    expected = random_expectation()
    assert expected['average_matches'] == pytest.approx(0.8)
    assert sum(expected['match_probabilities'].values()) == pytest.approx(1)
    assert expected['match_probabilities'][6] == pytest.approx(1/8145060)
    result = run_backtest(history, RandomModel, min_train=3, tickets=2, repeats=2)
    result['matches'] = [0,1,2,3,4,5,6,0,1] * 4
    summary = summarize(result, seed=3)
    assert summary['total_tickets'] == 36
    assert summary['target_draws'] == 9
    assert summary['best_result'] == 6
    assert summary['match_distribution'][0] == 8
    assert summary['rate_3_plus'] == pytest.approx(4/9)
    assert summary['rate_4_plus'] == pytest.approx(3/9)
    assert summary['rate_5_plus'] == pytest.approx(2/9)
    assert len(summary['mean_matches_ci95']) == 2
    assert summary['warnings']
