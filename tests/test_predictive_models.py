import importlib.util

import numpy as np
import pandas as pd
import pytest

from src.models.predictive import (LogisticModel, SimilarityModel, ForestModel,
                                   BoostingModel, TrainingTransform, rank_numbers, weighted_ticket)


@pytest.fixture
def rows():
    rng = np.random.default_rng(9)
    return pd.DataFrame([dict(target_draw=t, feature_cutoff=t-1, number=n,
                              target_date=pd.Timestamp('2020-01-01')+pd.Timedelta(days=7*t),
                              appeared_next=int(n in rng.choice(np.arange(1,46),6,replace=False)),
                              current_gap=float((t+n)%11), mean_gap=7.5)
                         for t in range(105,125) for n in range(1,46)])


def test_transform_training_only_and_number_identity(rows):
    transform = TrainingTransform(['current_gap','mean_gap','number']).fit(rows)
    means = transform.means.copy()
    current = rows.tail(45).copy()
    current['current_gap'] = 1e8
    output = transform.transform(current)
    assert output.shape == (45,47)
    np.testing.assert_array_equal(transform.means,means)
    assert means[0] == pytest.approx(rows.current_gap.mean())


def test_similarity_past_same_number_diagnostics(rows):
    model = SimilarityModel(columns=['current_gap','mean_gap'], k=5).fit(rows, cutoff=124)
    current = rows.tail(45).drop(columns='appeared_next').copy()
    current['target_draw'], current['feature_cutoff'] = 125,124
    scores = model.score_rows(current)
    assert len(scores)==45
    diagnostic = model.explain(current,17)
    assert diagnostic['score']==scores[17]
    assert len(diagnostic['neighbors']) == 5
    assert all(n['number']==17 and n['target_draw'] < 125 for n in diagnostic['neighbors'])
    assert 0 <= diagnostic['score'] <= 1
    with pytest.raises(ValueError): model.score_rows(rows.tail(45))
    with pytest.raises(ValueError): SimilarityModel(columns=['current_gap']).fit(rows,cutoff=123)


@pytest.mark.parametrize('factory',[LogisticModel,ForestModel,BoostingModel])
def test_model_determinism(rows,factory):
    if factory is ForestModel and importlib.util.find_spec('sklearn') is None:
        pytest.skip('scikit-learn unavailable')
    if factory is BoostingModel and not any(importlib.util.find_spec(x) for x in ('lightgbm','xgboost')):
        pytest.skip('LightGBM and XGBoost unavailable')
    current=rows.tail(45).drop(columns='appeared_next').copy()
    current['target_draw'],current['feature_cutoff']=125,124
    a=factory(columns=['current_gap','mean_gap'],seed=42).fit(rows,cutoff=124)
    b=factory(columns=['current_gap','mean_gap'],seed=42).fit(rows,cutoff=124)
    assert a.score_rows(current)==b.score_rows(current)
    assert a.training_cutoff == 124


def test_logistic_intercept_and_feature_importance(rows):
    model=LogisticModel(columns=['mean_gap']).fit(rows,cutoff=124)
    # Constant predictors reduce to a fitted intercept with no class weighting.
    assert model.intercept_probability == pytest.approx(rows.appeared_next.mean(),abs=1e-5)
    assert len(model.importance())==1


def test_rank_and_weighted_tickets():
    scores={n:float(n) for n in range(1,46)}
    assert rank_numbers(scores)[:6]==[45,44,43,42,41,40]
    ticket=weighted_ticket(scores,seed=20)
    assert ticket==weighted_ticket(scores,seed=20)
    assert len(set(ticket))==6 and all(1<=n<=45 for n in ticket)
    assert len(weighted_ticket({n:0. for n in range(1,46)},seed=1))==6
    with pytest.raises(ValueError): rank_numbers({1:.4})
    with pytest.raises(ValueError): weighted_ticket({n:-1. for n in range(1,46)},seed=1)


def test_reject_label_features(rows):
    with pytest.raises(ValueError): LogisticModel(columns=['appeared_next']).fit(rows,cutoff=124)
