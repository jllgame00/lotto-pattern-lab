"""Frozen Phase 21 series and independent auxiliary diagnostics."""
import hashlib
import importlib

import numpy as np
import pytest


def module():
    return importlib.import_module('src.analysis.long_memory_series')


def draws(n):
    x = np.zeros((n, 45), dtype=int)
    for i in range(n):
        x[i, (np.arange(6) * 7 + i) % 45] = 1
    return x


def test_frozen_series_are_aligned_and_prefix_causal():
    lm = module()
    x = draws(624)
    full = lm.build_series(x, cutoff=624)
    prefix = lm.build_series(x[:312], cutoff=312)
    assert full['values'].shape == (624, 55)
    assert full['cutoff'] == 624
    assert full['names'][:2] == ['number_01', 'number_02']
    assert full['names'][45:50] == [
        'shape_sum', 'shape_range', 'shape_std', 'shape_spacing_std', 'shape_odd_count']
    assert full['names'][50:] == [
        'band_01_09', 'band_10_18', 'band_19_27', 'band_28_36', 'band_37_45']
    assert full['groups'] == ['number'] * 45 + ['shape'] * 5 + ['band'] * 5
    np.testing.assert_array_equal(prefix['values'], full['values'][:312])
    np.testing.assert_allclose(full['values'][:, :45], x - 6 / 45)
    np.testing.assert_array_equal(full['values'][:, 50:].sum(axis=1), 6)
    assert full['representation_hash'] == hashlib.sha256(
        np.asarray(full['values'], dtype=np.float64).tobytes()).hexdigest()


def test_shape_coordinates_match_hand_checked_six_numbers():
    x = np.zeros((2, 45), dtype=int)
    x[:, np.array([1, 2, 3, 10, 20, 45]) - 1] = 1
    shape = module().build_series(x)['values'][:, 45:50]
    # Population variance of numbers = 2891/12; gaps = 1,1,7,10,25.
    np.testing.assert_allclose(shape, [[81, 44, np.sqrt(2891 / 12), np.sqrt(77.76), 3]] * 2)


@pytest.mark.parametrize('case', ['future', 'wrong_cutoff', 'not_six', 'not_binary', 'wrong_width'])
def test_research_boundary_rejects_invalid_or_future_input(case):
    x = draws(312)
    kwargs = {}
    if case == 'future':
        x = draws(1246)
    elif case == 'wrong_cutoff':
        kwargs['cutoff'] = 311
    elif case == 'not_six':
        x[0] = 0
    elif case == 'not_binary':
        x = x.astype(float)
        x[0, :2] = [.5, .5]
    elif case == 'wrong_width':
        x = x[:, :44]
    with pytest.raises(ValueError):
        module().build_series(x, **kwargs)


def test_aggregation_drops_tail_and_enforces_four_independent_blocks():
    result = module().aggregation(np.arange(1., 18.), blocks=(1, 2, 4, 8, 13))
    np.testing.assert_array_equal(result['blocks'], [1, 2, 4])
    np.testing.assert_array_equal(result['n_blocks'], [17, 8, 4])
    np.testing.assert_allclose(result['variance'][:, 0], [25.5, 24, 80 / 3])
    assert result['slope'].shape == (1,)
    np.testing.assert_allclose(result['deviation'], abs(result['slope'] + 1))


def test_white_noise_aggregation_slope_is_near_minus_one_for_long_synthetic():
    x = np.random.default_rng(21021).normal(size=(131072, 2))
    result = module().aggregation(x)
    np.testing.assert_allclose(result['slope'], -1, atol=.04)
    assert np.all(result['r2'] > .999)


def test_constant_aggregation_has_no_estimable_slope():
    result = module().aggregation(np.ones(312))
    assert not result['variance'].any()
    assert np.isnan(result['slope']).all()
    assert np.isnan(result['r2']).all()


def test_irrational_constant_columns_do_not_acquire_roundoff_memory():
    constant = np.full((312, 2), np.sqrt(2891 / 12))
    result = module().aggregation(constant)
    np.testing.assert_array_equal(result['variance'], np.zeros((7, 2)))
    assert np.isnan(result['slope']).all()
    spectrum = module().spectral_slope(constant)
    np.testing.assert_array_equal(spectrum['power'], np.zeros((11, 2)))
    assert np.isnan(spectrum['beta']).all()


@pytest.mark.parametrize('blocks', [(), (1, 1), (0, 2), (1., 2), (True, 2)])
def test_aggregation_rejects_invalid_block_grids(blocks):
    with pytest.raises(ValueError):
        module().aggregation(np.arange(312), blocks=blocks)


def test_spectrum_uses_fixed_long_period_band_and_negative_power_slope():
    n = 1040
    t = np.arange(n)
    x = sum(2 * k ** (-.7) * np.cos(2 * np.pi * k * t / n)
            for k in range(2, n // 26 + 1))
    result = module().spectral_slope(x)
    assert result['bins'] == 39
    np.testing.assert_allclose(result['frequency'], np.arange(2, 41) / n)
    np.testing.assert_allclose(result['beta'], [1.4], atol=1e-12)
    np.testing.assert_allclose(result['r2'], [1], atol=1e-12)
    np.testing.assert_allclose(result['power'][:, 0], n * np.arange(2., 41.) ** -1.4,
                               rtol=1e-12)
    repeat = module().spectral_slope(x + 100)
    np.testing.assert_allclose(repeat['power'], result['power'], rtol=1e-12)
    np.testing.assert_array_equal(module().spectral_slope(x)['power'], result['power'])


@pytest.mark.parametrize('bad', [np.ones((1, 20, 2)), [0, np.nan, 1], [], [1, np.inf]])
def test_auxiliary_math_rejects_nonfinite_empty_or_wrong_rank(bad):
    for name in ('aggregation', 'spectral_slope'):
        with pytest.raises(ValueError):
            getattr(module(), name)(bad)


def test_insufficient_auxiliary_support_is_explicit():
    with pytest.raises(ValueError):
        module().aggregation(np.arange(7), blocks=(2, 4))
    with pytest.raises(ValueError):
        module().spectral_slope(np.arange(77))


def test_rolling_grid_keeps_every_full_window_and_exact_final_cutoff():
    lm = module()
    np.testing.assert_array_equal(lm.rolling_endpoints(900, 624), [624, 676, 728, 780, 832, 884, 900])
    np.testing.assert_array_equal(lm.rolling_endpoints(416, 416), [416])
    np.testing.assert_array_equal(lm.rolling_endpoints(624, 312), np.arange(312, 625, 52))
    for n, window in [(1246, 312), (500, 313), (311, 312)]:
        with pytest.raises(ValueError):
            lm.rolling_endpoints(n, window)


def test_rolling_series_uses_only_completed_window_rows_and_absolute_draws():
    lm = module()
    x = draws(900)
    result = lm.rolling_series(x, 312, 728)
    np.testing.assert_array_equal(result['values'], lm.build_series(x[416:728])['values'])
    assert result['cutoff'] == 728
    assert result['start_draw'] == 417
    assert result['window'] == 312
    altered = x.copy()
    altered[728:] = draws(900 - 728)
    np.testing.assert_array_equal(lm.rolling_series(altered, 312, 728)['values'], result['values'])
    with pytest.raises(ValueError):
        lm.rolling_series(draws(1246), 312, 728)
    for window, end in [(313, 728), (312, 311), (312, 901)]:
        with pytest.raises(ValueError):
            lm.rolling_series(x, window, end)
