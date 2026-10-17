"""Independent count fixtures and causal, row-six event simulations."""
import importlib

import numpy as np
import pytest


def module():
    return importlib.import_module('src.analysis.point_process')


def fixture(events):
    """Number zero follows events; five/six fixed fillers keep rows valid."""
    x = np.zeros((len(events), 45), dtype=int)
    for t, event in enumerate(events):
        x[t, 0] = event
        x[t, 10:16 - int(event)] = 1
    return x


def test_event_gaps_are_before_target_and_relative_uses_only_completed_intervals():
    pp = module()
    x = fixture([0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0])
    h = pp.event_history(x)
    np.testing.assert_array_equal(h['events'][0], [2, 5, 10])
    np.testing.assert_array_equal(h['interarrivals'][0], [3, 5])
    np.testing.assert_array_equal(h['gaps'][:, 0], [-1, -1, 0, 1, 2, 0, 1, 2, 3, 4, 0])
    assert np.isnan(h['relative'][:5, 0]).all()
    np.testing.assert_allclose(h['relative'][5:, 0], [0, 1/3, 2/3, 1, 4/3, 0])
    assert h['current_gap'][0] == 1
    assert h['current_relative'][0] == .25
    assert h['current_gap'][44] == -1
    assert np.isnan(h['current_relative'][44])
    for end in (6, 9, 10):
        prefix = pp.event_history(x[:end])
        np.testing.assert_allclose(prefix['relative'], h['relative'][:end], equal_nan=True)
        np.testing.assert_allclose(prefix['current_relative'], h['relative'][end], equal_nan=True)
        np.testing.assert_array_equal(prefix['current_gap'], h['gaps'][end])


def test_recent_counts_include_the_completed_current_draw_and_are_fresh():
    pp = module()
    x = fixture([1] * 60)
    h = pp.event_history(x)
    assert [h['recent_counts'][w][-1, 0] for w in (10, 26, 52)] == [10, 26, 52]
    assert h['recent_counts'][10][0, 0] == 1
    h['gaps'][:] = 900
    assert pp.event_history(x)['gaps'][1, 0] == 0


def test_renewal_state_edges_current_and_censoring():
    pp = module()
    x = fixture([1] + [0] * 30)
    s = pp.renewal_states(x, 'clipped')
    assert s[0, 0] == -1 and s[1, 0] == 0 and s[-1, 0] == 26
    coarse = pp.renewal_states(x, 'coarse')
    np.testing.assert_array_equal(coarse[[1, 2, 4, 8, 14, 27], 0], [0, 1, 2, 3, 4, 5])
    assert pp.current_renewal_state(x, 'clipped')[0] == 26
    assert pp.current_renewal_state(x, 'relative')[0] == -1
    y = fixture([1, 0, 1] + [0] * 9)
    relative = pp.renewal_states(y, 'relative')
    np.testing.assert_array_equal(relative[[3, 4, 5, 7, 9], 0], [0, 1, 2, 3, 4])
    assert pp.current_renewal_state(y, 'relative')[0] == 4


def test_renewal_counts_shrink_to_own_eligible_baseline():
    pp = module()
    table = pp.renewal_table(fixture([1, 1, 0, 1, 0, 0]), 'clipped', alpha=26, minimum=1)
    # Eligible rows 2..6: outcomes 1,0,1,0,0; gap zero has 3 rows and 1 hit.
    assert table['support'].shape == (45, 27)
    np.testing.assert_array_equal(table['support'][0, :3], [3, 2, 0])
    np.testing.assert_array_equal(table['hits'][0, :3], [1, 1, 0])
    assert table['baseline'][0] == .2
    assert table['rate'][0, 0] == pytest.approx(1/3)
    assert table['conditional'][0, 0] == pytest.approx(6.2/29)
    assert table['effect'][0, 0] == pytest.approx(6.2/29 - .2)
    assert table['score'][0, 0] == pytest.approx(abs(6.2/29 - .2) * np.sqrt(3/.16))
    assert np.isnan(table['rate'][0, 2])
    assert table['conditional'][0, 2] == .2
    assert not table['eligible'][0, 2]
    assert not table['eligible'][44].any()


def test_lag_source_target_counts_sign_and_sparse_fallback():
    pp = module()
    x = np.zeros((6, 45), dtype=int)
    pairs = [(0,), (1,), (0,), (1,), (0,), (1,)]
    for t, pair in enumerate(pairs):
        x[t, list(pair)] = 1
        x[t, 10:15] = 1
    e = pp.lag_effects(x, 1, alpha=26, minimum=1)
    assert e['n'] == 5
    assert e['support'][0, 1] == 3 and e['hits'][0, 1] == 3
    assert e['support'][1, 0] == 2 and e['hits'][1, 0] == 2
    assert e['baseline'][0, 1] == .25 and e['baseline'][1, 0] == .2
    assert e['conditional'][0, 1] == pytest.approx(9.5/29)
    assert e['rate'][0, 1] == 1
    assert e['lift'][0, 1] == pytest.approx((9.5/29)/.25)
    assert e['effect'][0, 1] > 0 and e['effect'][0, 0] < 0
    assert e['log_odds'][0, 1] > 0 and e['score'][0, 0] < 0
    assert np.isnan(e['rate'][44, 0])
    assert e['conditional'][44, 0] == e['baseline'][44, 0]
    assert e['score'][44, 0] == 0 and not e['eligible'][44, 0]


def test_lags_longer_than_history_are_neutral_with_no_support():
    pp = module()
    e = pp.lag_effects(fixture([1, 0]), 26)
    assert e['n'] == 0
    assert not e['support'].any() and not e['eligible'].any()
    np.testing.assert_allclose(e['conditional'], 2/15)
    k = pp.kernel_effects(fixture([1, 0]))
    assert np.isnan(k['score']).all() and not k['eligible'].any()


def planted(seed=221, n=1245):
    """Causal self/cross excitation and inhibition with exactly six events."""
    rng = np.random.default_rng(seed)
    x = np.zeros((n, 45), dtype=int)
    for t in range(n):
        weight = np.ones(45)
        if t:
            weight[0] = 24 if x[t-1, 0] else .12
            weight[1] = 40 if x[t-1, 2] else .2
            weight[3] = .001 if x[t-1, 4] else 3
        chosen = rng.choice(45, 6, replace=False, p=weight/weight.sum())
        x[t, chosen] = 1
    return x


def test_valid_row_six_simulation_recovers_self_cross_and_inhibition():
    pp = module()
    x = planted()
    e = pp.all_effects(x)
    assert e['score'].shape == (7, 45, 45)
    assert tuple(e['lags']) == (1, 2, 3, 4, 8, 13, 26)
    assert e['score'][0, 0, 0] > 5
    assert e['score'][0, 2, 1] > 5
    assert e['score'][0, 4, 3] < -1
    assert e['score'][0, 2, 1] > e['score'][0, 1, 2] + 4
    k = pp.kernel_effects(x, effects=e)
    assert tuple(k['names']) == ('exp2', 'exp8', 'finite')
    assert k['score'].shape == (3, 45, 45)
    assert k['eligible'][:, 2, 1].all()
    assert k['score'][0, 2, 1] > 20
    assert k['amplitude'][0, 2, 1] > 0
    assert k['amplitude'][0, 4, 3] < 0
    second = pp.all_effects(x)
    for key in ('support', 'hits', 'effect', 'score', 'eligible'):
        np.testing.assert_array_equal(e[key], second[key])


def test_kernel_projection_uses_variance_and_squared_signed_scores():
    pp = module()
    x = fixture([1, 0] * 40)
    shape = (7, 45, 45)
    effects = {'effect': np.full(shape, .1), 'support': np.full(shape, 100),
               'baseline': np.full(shape, .2), 'score': np.full(shape, 2.5),
               'eligible': np.ones(shape, bool)}
    k = pp.kernel_effects(x, effects=effects)
    w = np.exp(-(np.array([1, 2, 3, 4, 8, 13, 26])-1)/2)
    assert k['score'][0, 0, 0] == pytest.approx((10*w.sum())**2/(16*(w*w).sum()))
    assert k['amplitude'][0, 0, 0] == pytest.approx(.1*w.sum()/(w*w).sum())
    assert k['score'][2, 0, 0] == pytest.approx(6.25)
    assert k['amplitude'][2, 0, 0] == pytest.approx(.1)
    effects['eligible'][4, 0, 0] = False
    effects['support'][:, 1, 1] = 0
    k = pp.kernel_effects(x, effects=effects)
    assert not k['eligible'][:, 0, 0].any()
    assert np.isnan(k['score'][:, 1, 1]).all()


@pytest.mark.parametrize('lag', [0, -1, 5, 1.0, True, '1'])
def test_rejects_undeclared_or_noninteger_lags(lag):
    with pytest.raises(ValueError):
        module().lag_effects(fixture([1, 0] * 20), lag)


@pytest.mark.parametrize('kwargs', [{'alpha': 0}, {'alpha': np.nan}, {'alpha': True},
                                   {'minimum': 0}, {'minimum': 1.5}, {'minimum': True}])
def test_rejects_invalid_smoothing_and_support(kwargs):
    pp = module()
    x = fixture([1, 0] * 20)
    for function, args in ((pp.lag_effects, (x, 1)), (pp.all_effects, (x,)),
                           (pp.kernel_effects, (x,)), (pp.renewal_table, (x, 'coarse'))):
        with pytest.raises(ValueError):
            function(*args, **kwargs)


def test_rejects_invalid_schemes_matrices_and_draw_1246():
    pp = module()
    for function in (pp.renewal_states, pp.current_renewal_state, pp.renewal_table):
        with pytest.raises(ValueError):
            function(fixture([1, 0]), 'unknown')
    for x in (np.zeros((2, 45)), np.zeros((2, 44)), fixture([1]*1246), fixture([1])):
        for function in (pp.event_history, pp.all_effects, pp.kernel_effects):
            with pytest.raises(ValueError):
                function(x)
