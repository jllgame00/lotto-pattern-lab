"""Synthetic causal and support checks for H18's historical models."""
import importlib.util
import json

import numpy as np
import pytest

from src.analysis.spatiotemporal import iid_surrogate


def planted(n=319):
    x = np.zeros((n, 45), dtype=bool)
    x[:156, :6] = True
    x[156:, 6:12] = True
    return x


def test_change_point_models_module_exists():
    assert importlib.util.find_spec('src.models.change_point') is not None


@pytest.mark.parametrize('representation', ['A', 'B13', 'B26', 'B52', 'C'])
def test_planted_last_boundary_and_shrinkage_include_incomplete_tail(representation):
    from src.models.change_point import RegimeFrequencyModel

    x = planted()
    model = RegimeFrequencyModel(representation=representation, minimum=104, shrinkage=26)
    scores = model.fit(x, cutoff=319).score_matrix(x, target=320)
    state = model.last_state
    assert state['last_change_point'] == 156
    assert state['boundaries'] == [156]
    assert state['segment_length'] == 163
    assert state['training_cutoff'] == model.score_training_cutoff == 319
    assert state['representation'] == representation
    np.testing.assert_array_equal(state['segment_rates'], [0]*6 + [1]*6 + [0]*33)
    want = (x[156:].sum(axis=0) + 26*x.mean(axis=0)) / 189
    np.testing.assert_allclose([scores[i] for i in range(1,46)], want)
    np.testing.assert_allclose(state['current_rates'], want)
    assert sum(scores.values()) == pytest.approx(6)
    assert set(scores) == set(range(1,46))
    json.dumps(state, allow_nan=False)
    if representation.startswith('B'):
        block = int(representation[1:])
        assert state['discarded_tail'] == 319 % block
        assert state['segmentation_used_draws'] == 319 // block * block
        assert state['effective_minimum'] == ((104+block-1)//block)*block


@pytest.mark.parametrize('representation', ['A', 'B13', 'B26', 'B52', 'C'])
def test_constant_history_has_no_boundaries_and_finite_long_term_rates(representation):
    from src.models.change_point import RegimeFrequencyModel
    x = np.zeros((104,45), dtype=bool)
    x[:, :6] = True
    model = RegimeFrequencyModel(representation=representation).fit(x, cutoff=104)
    scores = model.score_matrix(x, target=105)
    assert model.last_state['last_change_point'] == 0
    assert model.last_state['boundaries'] == []
    assert model.last_state['segment_length'] == 104
    np.testing.assert_array_equal(list(scores.values()), [1]*6+[0]*39)
    assert len(model.last_diagnostic) == 45
    assert all(row['segment_length'] == 104 for row in model.last_diagnostic)


@pytest.mark.parametrize('factory', ['regime', 'baseline'])
def test_outer_cadence_recomputes_on_unchanged_extended_prefix(factory):
    from src.models.change_point import AdaptiveWindowBaseline, RegimeFrequencyModel
    constructor = RegimeFrequencyModel if factory == 'regime' else AdaptiveWindowBaseline
    x = iid_surrogate(160, seed=1919)
    early = constructor().fit(x[:120], cutoff=120)
    fresh = constructor().fit(x[:150], cutoff=150)
    scores = early.score_matrix(x[:150], target=151)
    assert scores == fresh.score_matrix(x[:150], target=151)
    assert early.score_training_cutoff == 150
    assert early.training_cutoff == 120
    changed = x[:150].copy()
    changed[0] = np.roll(changed[0], 1)
    with pytest.raises(ValueError, match='prefix|training'):
        early.score_matrix(changed, target=151)
    # Mutating the caller's fit argument cannot rewrite the stored binding.
    original = x[:120].copy()
    bound = constructor().fit(original, cutoff=120)
    original[0] = np.roll(original[0], 1)
    with pytest.raises(ValueError):
        bound.score_matrix(original, target=121)


@pytest.mark.parametrize('factory', ['regime', 'baseline'])
def test_future_rows_sealed_target_unfitted_and_invalid_cutoffs_are_rejected(factory):
    from src.models.change_point import AdaptiveWindowBaseline, RegimeFrequencyModel
    constructor = RegimeFrequencyModel if factory == 'regime' else AdaptiveWindowBaseline
    x = iid_surrogate(150, seed=1920)
    model = constructor().fit(x[:120], cutoff=120)
    for matrix, target in [(x,121), (x[:119],120), (x[:120],120),
                            (x[:120],121.0), (iid_surrogate(1245,seed=1),1246)]:
        with pytest.raises(ValueError):
            model.score_matrix(matrix, target=target)
    with pytest.raises(ValueError):
        constructor().score_matrix(x, target=151)
    for cutoff in (119,121,120.0,True):
        with pytest.raises(ValueError):
            constructor().fit(x[:120], cutoff=cutoff)


@pytest.mark.parametrize('window', [26,52,104])
def test_fixed_baseline_uses_exact_last_window_and_reports_support(window):
    from src.models.change_point import AdaptiveWindowBaseline
    x = iid_surrogate(150, seed=1921)
    model = AdaptiveWindowBaseline(window=window).fit(x, cutoff=150)
    scores = model.score_matrix(x, target=151)
    np.testing.assert_allclose(list(scores.values()), x[-window:].mean(axis=0))
    assert model.last_state['segment_length'] == window
    assert model.last_state['last_change_point'] == 150-window
    with pytest.raises(ValueError):
        AdaptiveWindowBaseline(window=window).fit(x[:window-1], cutoff=window-1)


def test_regime_history_minimum_and_block52_minimum_rounding_are_explicit():
    from src.models.change_point import RegimeFrequencyModel
    with pytest.raises(ValueError):
        RegimeFrequencyModel().fit(iid_surrogate(103, seed=1), cutoff=103)
    x = planted()
    for minimum in (26,52):
        model = RegimeFrequencyModel(representation='B52', minimum=minimum).fit(x, cutoff=319)
        model.score_matrix(x, target=320)
        assert model.last_state['effective_minimum'] == 52
        assert model.last_state['penalty'] == pytest.approx(45*np.log(6))


@pytest.mark.parametrize('kwargs', [dict(representation='number'), dict(representation='B10'),
    dict(minimum=25), dict(minimum=26.0), dict(multiplier=True), dict(multiplier=3),
    dict(shrinkage=0), dict(shrinkage=26.0)])
def test_regime_grid_rejects_undeclared_or_nonstrict_parameters(kwargs):
    from src.models.change_point import RegimeFrequencyModel
    with pytest.raises(ValueError):
        RegimeFrequencyModel(**kwargs)


@pytest.mark.parametrize('window', [10, True, 26.0])
def test_baseline_grid_rejects_undeclared_or_nonstrict_windows(window):
    from src.models.change_point import AdaptiveWindowBaseline
    with pytest.raises(ValueError):
        AdaptiveWindowBaseline(window=window)


def test_harness_construct_and_capture_audits_real_model_state():
    from src.backtest.change_point import _CaptureState, candidates, construct, construct_baseline
    x = planted()
    config = next(iter(candidates().values()))
    captured = []
    model = _CaptureState(construct(config), captured, config['representation']).fit(x[:280], cutoff=280)
    scores = model.score_matrix(x, target=320)
    assert captured[0]['diagnostics_available']
    assert captured[0]['source_cutoff'] == 319
    assert captured[0]['last_change_point'] == 156
    np.testing.assert_array_equal(json.loads(captured[0]['segment_rates']), x[156:].mean(axis=0))
    assert len(scores) == 45
    assert len(construct_baseline(26).fit(x,cutoff=319).score_matrix(x,target=320)) == 45


def test_all_sixty_configs_share_prefix_context_and_thirty_segmentation_fits():
    from src.backtest.change_point import candidates, construct
    from src.models.change_point import _contexts, _fits
    _contexts.cache_clear()
    _fits.cache_clear()
    x = iid_surrogate(120,seed=1922)
    for config in candidates().values():
        model = construct(config).fit(x.copy(), cutoff=120)
        assert len(model.score_matrix(x.copy(), target=121)) == 45
    assert _contexts.cache_info().misses == 1
    assert _contexts.cache_info().maxsize == 2
    assert _fits.cache_info().misses == 30
    assert _fits.cache_info().hits == 30
    assert _fits.cache_info().maxsize == 30
    changed = np.roll(x, 1, axis=1)
    first = construct(next(iter(candidates().values())))
    first.fit(changed, cutoff=120).score_matrix(changed,target=121)
    assert _contexts.cache_info().misses == 2
    assert _fits.cache_info().misses == 31
