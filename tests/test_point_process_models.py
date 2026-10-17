"""Frozen causal renewal and event influence models, using synthetic row-six data."""
import importlib.util
import json

import numpy as np
import pytest
from scipy.special import expit, logit

from src.analysis.spatiotemporal import iid_surrogate


def signal(n=520, *, inhibitory=False):
    rng = np.random.default_rng(200043)
    x = np.zeros((n, 45), dtype=bool)
    for t in range(n):
        own = rng.random() < .35
        target = t > 0 and (not x[t-1, 0] if inhibitory else x[t-1, 0])
        x[t, :2] = own, target
        x[t, rng.choice(np.arange(2, 45), 6-int(own)-int(target), replace=False)] = True
    return x


def test_models_module_exists():
    assert importlib.util.find_spec('src.models.point_process') is not None


@pytest.mark.parametrize('name', ['RenewalModel', 'HawkesInfluenceModel', 'SignedInfluenceModel'])
def test_binding_rejects_mutated_training_future_rows_and_sealed_targets(name):
    from src.models import point_process as models
    constructor = getattr(models, name)
    x = iid_surrogate(325, seed=200041)
    model = constructor().fit(x[:300], cutoff=300)
    assert not model.training.flags.writeable
    for values, target in [(x, 301), (x[:300], 300), (x[:300], 301.0),
                           (iid_surrogate(1245, seed=5), 1246)]:
        with pytest.raises(ValueError):
            model.score_matrix(values, target=target)
    changed = x.copy()
    changed[0] = np.roll(changed[0], 1)
    with pytest.raises(ValueError, match='prefix|training'):
        model.score_matrix(changed, target=326)
    for cutoff in (299, 301, 300.0, True):
        with pytest.raises(ValueError):
            constructor().fit(x[:300], cutoff=cutoff)
    with pytest.raises(ValueError):
        constructor().score_matrix(x[:300], target=301)


@pytest.mark.parametrize('scheme', ['clipped', 'coarse', 'relative'])
def test_renewal_table_freezes_and_unsupported_state_uses_target_baseline(scheme):
    from src.analysis.point_process import current_renewal_state, renewal_table
    from src.models.point_process import RenewalModel
    x = iid_surrogate(325, seed=200042)
    model = RenewalModel(scheme=scheme, alpha=104).fit(x[:300], cutoff=300)
    table = renewal_table(x[:300], scheme, alpha=104, minimum=20)
    scores = model.score_matrix(x, target=326)
    states = current_renewal_state(x, scheme)
    for j, state in enumerate(states):
        supported = state >= 0 and table['support'][j, state] >= 20
        expected = table['conditional'][j, state] if supported else table['baseline'][j]
        assert scores[j+1] == pytest.approx(expected)
        row = model.last_diagnostic[j]
        assert row['training_cutoff'] == 300 and row['source_cutoff'] == 325
    assert model.configuration()['scheme'] == scheme
    json.dumps(model.last_diagnostic, allow_nan=False)


@pytest.mark.parametrize('kernel', ['exp2', 'exp8', 'finite'])
def test_edge_selection_has_source_to_target_direction_and_frozen_training(kernel):
    from src.models.point_process import HawkesInfluenceModel
    x = signal()
    model = HawkesInfluenceModel(kernel=kernel, incoming=3).fit(x[:480], cutoff=480)
    assert model.selected_edges[1][0]['source'] == 1
    before = json.dumps(model.selected_edges, sort_keys=True)
    beta = model.coefficients.copy()
    scores = model.score_matrix(x, target=521)
    assert set(scores) == set(range(1, 46))
    assert np.all((np.array(list(scores.values())) >= 1e-6) &
                  (np.array(list(scores.values())) <= 1-1e-6))
    assert json.dumps(model.selected_edges, sort_keys=True) == before
    np.testing.assert_array_equal(model.coefficients, beta)
    assert len(model.last_diagnostic) == 45
    assert model.last_diagnostic[1]['source_cutoff'] == 520
    assert model.last_diagnostic[1]['training_cutoff'] == 480
    for row in model.last_diagnostic:
        assert sum(edge['contribution'] for edge in row['incoming']) == pytest.approx(row['cross_contribution'])
    for j, edges in enumerate(model.selected_edges):
        assert len(edges) <= 3
        assert sum(abs(e['amplitude']) for e in edges) <= 1 + 1e-12
        for edge in edges:
            assert edge['source'] != j+1 and edge['support'] >= 30
            assert edge['amplitude'] >= 0
            assert np.min(edge['lag_weights']) >= 0
    json.dumps(model.last_diagnostic, allow_nan=False)


def test_current_events_change_features_without_retraining_and_no_training_mutation():
    from src.models.point_process import HawkesInfluenceModel
    x = signal()
    model = HawkesInfluenceModel().fit(x[:480], cutoff=480)
    x2 = x.copy()
    x2[-1] = np.roll(x2[-1], 1)
    a = model.score_matrix(x, target=521)
    b = model.score_matrix(x2, target=521)
    assert a != b
    assert np.max(np.abs(model.last_features)) <= 3
    fit_argument = x[:480].copy()
    immutable = HawkesInfluenceModel().fit(fit_argument, cutoff=480)
    fit_argument[0] = np.roll(fit_argument[0], 1)
    with pytest.raises(ValueError):
        immutable.score_matrix(fit_argument, target=481)


def test_inhibition_is_separate_from_nonnegative_hawkes():
    from src.models.point_process import HawkesInfluenceModel, SignedInfluenceModel
    x = signal(inhibitory=True)
    positive = HawkesInfluenceModel(incoming=1).fit(x, cutoff=len(x))
    signed = SignedInfluenceModel(incoming=1).fit(x, cutoff=len(x))
    edge = signed.selected_edges[1][0]
    assert edge['source'] == 1 and edge['amplitude'] < 0
    assert edge['strength'] == pytest.approx(np.dot(signed.self_weights, np.abs(edge['lag_effects'])))
    assert all(e['amplitude'] >= 0 for group in positive.selected_edges for e in group)
    assert np.all(positive.coefficients >= 0)
    assert signed.configuration()['signed'] is True


def test_pooled_analytic_gradient_and_fit_improve_objective_with_nested_self_fit():
    from src.models.point_process import HawkesInfluenceModel, _ridge_objective
    x = signal()
    model = HawkesInfluenceModel(ridge=10).fit(x, cutoff=len(x))
    features, outcomes, offsets = model.training_features, model.training_outcomes, model.training_offsets
    beta = np.array([.3, .7])
    value, gradient = _ridge_objective(beta, features, outcomes, offsets, 10)
    numeric = np.array([(_ridge_objective(beta+np.eye(2)[k]*1e-5, features, outcomes, offsets, 10)[0]
                       -_ridge_objective(beta-np.eye(2)[k]*1e-5, features, outcomes, offsets, 10)[0])/2e-5
                       for k in range(2)])
    np.testing.assert_allclose(gradient, numeric, atol=1e-5)
    assert np.isfinite(value)
    assert model.optimization_diagnostics['objective'] < model.optimization_diagnostics['baseline_objective']
    assert np.all((model.coefficients >= 0) & (model.coefficients <= 3))
    scores = model.self_only_scores(x, target=len(x)+1)
    expected = expit(logit(model.baseline) + model.self_coefficient*model.last_features[:, 0])
    np.testing.assert_allclose(list(scores.values()), expected)
    self_value = _ridge_objective(np.array([model.self_coefficient]), features[:, :1], outcomes, offsets, 10)[0]
    grid = [_ridge_objective(np.array([v]), features[:, :1], outcomes, offsets, 10)[0] for v in np.linspace(0, 3, 61)]
    assert self_value <= min(grid)+1e-6


def test_preparation_shared_across_ridges_but_not_prefixes():
    from src.models.point_process import HawkesInfluenceModel, _prepared_training
    _prepared_training.cache_clear()
    x = signal(n=310)
    a = HawkesInfluenceModel(ridge=1).fit(x, cutoff=310)
    b = HawkesInfluenceModel(ridge=10).fit(x.copy(), cutoff=310)
    assert _prepared_training.cache_info().misses == 1
    assert _prepared_training.cache_info().hits == 1
    np.testing.assert_array_equal(a.training_features, b.training_features)


def test_training_features_are_reconstructible_from_strictly_earlier_events():
    from src.analysis.point_process import LAGS
    from src.models.point_process import HawkesInfluenceModel
    x = signal()
    model = HawkesInfluenceModel(kernel='exp8', incoming=3).fit(x, cutoff=len(x))
    indices = model.training_outcome_indices
    assert indices[0] == len(x)-416 and indices[-1] == len(x)-1
    raw = np.zeros((len(indices), 45, 2))
    for lag, weight in zip(LAGS, model.self_weights):
        raw[:, :, 0] += x[indices-lag]*weight
    for j, edges in enumerate(model.selected_edges):
        for edge in edges:
            for lag, weight in zip(LAGS, edge['lag_weights']):
                raw[:, j, 1] += x[indices-lag, edge['source']-1]*weight*edge['amplitude']/len(edges)
    np.testing.assert_allclose(model.feature_means, raw.mean(axis=0))
    expected = np.clip((raw-model.feature_means)/model.feature_scales, -3, 3).reshape(-1, 2)
    np.testing.assert_allclose(model.training_features, expected)
    np.testing.assert_array_equal(model.training_outcomes.reshape(-1, 45), x[indices])


def test_positive_event_impulse_cannot_reduce_target_probability():
    from src.models.point_process import HawkesInfluenceModel
    x = signal()
    model = HawkesInfluenceModel().fit(x[:480], cutoff=480)
    absent = x.copy()
    present = x.copy()
    absent[-1] = False
    present[-1] = False
    absent[-1, 2:8] = True
    present[-1, [0, 3, 4, 5, 6, 7]] = True
    low = model.score_matrix(absent, target=len(x)+1)[2]
    high = model.score_matrix(present, target=len(x)+1)[2]
    assert model.coefficients[1] > 0
    assert high > low


def test_finite_signed_kernel_retains_lag_directions_and_unsupported_numbers_are_neutral():
    from src.models.point_process import HawkesInfluenceModel, SignedInfluenceModel
    x = signal(inhibitory=True)
    model = SignedInfluenceModel(kernel='finite').fit(x, cutoff=len(x))
    edge = model.selected_edges[1][0]
    assert edge['source'] == 1 and edge['lag_weights'][0] < 0
    assert np.abs(edge['lag_weights']).sum() == pytest.approx(1)
    fixed = np.zeros((300, 45), dtype=bool)
    fixed[:, :6] = True
    positive = HawkesInfluenceModel().fit(fixed, cutoff=300)
    scores = positive.score_matrix(fixed, target=301)
    self_scores = positive.self_only_scores(fixed, target=301)
    for j in range(6, 45):
        assert positive.selected_edges[j] == []
        assert positive.last_features[j, 1] == 0
        assert scores[j+1] == self_scores[j+1] == pytest.approx(positive.baseline[j])


@pytest.mark.parametrize('kernel', ['exp2', 'exp8', 'finite'])
@pytest.mark.parametrize('signed', [False, True])
def test_source_is_excluded_if_any_declared_lag_is_unsupported(monkeypatch, kernel, signed):
    from src.models import point_process as models
    shape = (7, 45, 45)
    effects = dict(support=np.zeros(shape, dtype=int), eligible=np.zeros(shape, dtype=bool),
                   effect=np.zeros(shape), log_odds=np.zeros(shape))
    # Source1 -> target2 is very strong, but its lag26 cell is unsupported.
    effects['support'][:, 0, 1] = 100
    effects['support'][-1, 0, 1] = 29
    effects['eligible'][:, 0, 1] = True
    effects['eligible'][-1, 0, 1] = False
    effects['effect'][:, 0, 1] = -.5 if signed else .5
    effects['log_odds'][:, 0, 1] = -2 if signed else 2
    monkeypatch.setattr(models, 'all_effects', lambda *args, **kwargs: effects)
    edges = models._select_edges(iid_surrogate(300, seed=200045), kernel, 3, 26, signed)
    assert edges[1] == []


def test_canonical_prefix738_boundary_optimum_does_not_fail_on_sum_loss_roundoff():
    from pathlib import Path
    from src.analysis.spatiotemporal import lotto_matrix
    from src.models.point_process import HawkesInfluenceModel, _ridge_objective
    from src.recurrence_cli import load_research_source
    source = Path(__file__).resolve().parents[1]/'data/raw/lotto_history.csv'
    history = load_research_source(source)
    x = lotto_matrix(history[history.draw_no <= 738], cutoff=738)
    model = HawkesInfluenceModel(kernel='exp8', incoming=3, alpha=104, ridge=1).fit(x, cutoff=738)
    objective, gradient = _ridge_objective(model.coefficients, model.training_features,
        model.training_outcomes, model.training_offsets, model.ridge)
    projected = gradient.copy()
    projected[(model.coefficients <= 1e-9) & (gradient > 0)] = 0
    projected[(model.coefficients >= 3-1e-9) & (gradient < 0)] = 0
    assert np.max(np.abs(projected))/len(model.training_outcomes) <= 1e-8
    assert objective <= model.optimization_diagnostics['baseline_objective']
    assert model.coefficients[0] == pytest.approx(.041998381887, abs=1e-6)
    assert model.coefficients[1] == pytest.approx(3)
    assert model.optimization_diagnostics['projected_kkt_per_row'] <= 1e-8


def test_solver_never_accepts_an_unsuccessful_result_even_at_stationarity(monkeypatch):
    from src.models import point_process as models
    original = models.minimize
    def unsuccessful(*args, **kwargs):
        result = original(*args, **kwargs)
        result.success = False
        return result
    monkeypatch.setattr(models, 'minimize', unsuccessful)
    with pytest.raises(RuntimeError, match='optimization'):
        models.HawkesInfluenceModel().fit(signal(n=300), cutoff=300)


@pytest.mark.parametrize('kwargs', [dict(kernel='other'), dict(incoming=2), dict(alpha=0),
    dict(ridge=0), dict(incoming=True), dict(alpha=26.0), dict(ridge=1.0)])
def test_influence_grid_is_strict(kwargs):
    from src.models.point_process import HawkesInfluenceModel
    with pytest.raises(ValueError):
        HawkesInfluenceModel(**kwargs)
