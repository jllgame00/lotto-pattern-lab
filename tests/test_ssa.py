"""Numerical contracts for centered SSA; all fixtures are synthetic."""
import importlib.util

import numpy as np
import pytest


def test_ssa_module_exists():
    assert importlib.util.find_spec('src.analysis.ssa') is not None


def test_trajectory_and_antidiagonal_average():
    from src.analysis.ssa import diagonal_average, hankel
    np.testing.assert_array_equal(hankel([1, 2, 3, 4, 5, 6], 3),
                                  [[1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6]])
    np.testing.assert_allclose(diagonal_average([[1, 2, 3], [4, 5, 6]]),
                               [1, 3, 4, 6])


@pytest.mark.parametrize('x,L', [([1, 2, 3], 2), ([1, 2, 3, 4], 1),
    ([1, 2, 3, 4], 3), ([1, 2, 3, 4], 2.0), ([1, 2, 3, 4], True),
    ([[1, 2], [3, 4]], 2), ([1, 2, np.nan, 4], 2), ([1, 2, np.inf, 4], 2)])
def test_hankel_rejects_invalid_input(x, L):
    from src.analysis.ssa import hankel
    with pytest.raises(ValueError):
        hankel(x, L)


@pytest.mark.parametrize('matrix', [[], [[1, np.nan]], [1, 2], np.empty((2, 0))])
def test_diagonal_average_rejects_invalid_input(matrix):
    from src.analysis.ssa import diagonal_average
    with pytest.raises(ValueError):
        diagonal_average(matrix)


def test_full_reconstruction_and_spectrum_match_svd():
    from src.analysis.ssa import decompose, hankel
    x = 7 + np.random.default_rng(91).normal(size=90)
    result = decompose(x, 26, components=26)
    expected = np.linalg.svd(hankel(x - x.mean(), 26), compute_uv=False)
    np.testing.assert_allclose(result['singular_values'], expected, rtol=1e-12)
    np.testing.assert_allclose(result['energy_ratios'], expected ** 2 / sum(expected ** 2))
    np.testing.assert_allclose(result['components'].sum(axis=0) + result['mean'], x,
                               atol=2e-14)
    assert result['components'].shape == (26, 90)
    assert result['left_vectors'].shape == (26, 26)
    assert result['right_vectors'].shape == (26, 65)
    assert result['residual_variance'] < 1e-25


def test_centering_preserves_units_and_does_not_modify_input():
    from src.analysis.ssa import decompose
    x = np.sin(2 * np.pi * np.arange(400) / 16)
    original = x.copy()
    base = decompose(x, 48, components=2)
    scaled = decompose(10 + 3 * x, 48, components=2)
    np.testing.assert_allclose(scaled['components'], 3 * base['components'], atol=1e-12)
    np.testing.assert_allclose(scaled['singular_values'], 3 * base['singular_values'], atol=3e-6)
    assert scaled['mean'] == pytest.approx(10)
    assert scaled['residual_variance'] < 1e-25
    np.testing.assert_array_equal(x, original)
    np.testing.assert_array_equal(base['components'], decompose(x, 48, components=2)['components'])


def test_sinusoidal_pair_is_a_candidate_with_documented_units():
    from src.analysis.ssa import candidate_pairs, decompose
    x = 3 * np.sin(2 * np.pi * np.arange(416) / 16)
    result = decompose(x, 48)
    pair = candidate_pairs(result)[0]
    assert (pair['first'], pair['second']) == (0, 1)
    assert pair['period'] == pytest.approx(16)
    assert pair['energy_share'] == pytest.approx(1)
    assert pair['amplitude'] == pytest.approx(3 / np.sqrt(2))
    assert pair['spectral_concentration'] > .99
    assert 0 < pair['score'] <= 1
    assert candidate_pairs(result, min_period=20) == []


def test_balanced_broadband_components_do_not_make_a_pair():
    from src.analysis.ssa import candidate_pairs
    # Identical broadband spectra and balanced energies alone are insufficient.
    random = np.random.default_rng(3).normal(size=416)
    result = dict(singular_values=np.ones(2), energy_ratios=np.array([.5, .5]),
                  components=np.array([random, random]))
    assert candidate_pairs(result) == []


def test_recurrent_forecast_continues_selected_sinusoidal_subspace():
    from src.analysis.ssa import decompose, recurrent_forecast
    t = np.arange(416)
    x = 4 + 2 * np.cos(2 * np.pi * t / 16 + .2)
    prediction = recurrent_forecast(decompose(x, 48, components=2), [0, 1], steps=12)
    expected = 4 + 2 * np.cos(2 * np.pi * np.arange(416, 428) / 16 + .2)
    np.testing.assert_allclose(prediction, expected, atol=2e-12)
    assert recurrent_forecast(decompose(x, 48), [0, 1]).shape == (1,)


def test_constant_signal_has_zero_energy_and_no_candidate():
    from src.analysis.ssa import candidate_pairs, decompose
    result = decompose(np.full(100, 7.), 26)
    assert np.isfinite(result['energy_ratios']).all()
    assert result['energy_ratios'].sum() == 0
    assert result['residual_variance'] == 0
    assert candidate_pairs(result) == []


@pytest.mark.parametrize('components', [0, 27, 1.5, True])
def test_decompose_rejects_invalid_component_count(components):
    from src.analysis.ssa import decompose
    with pytest.raises(ValueError):
        decompose(np.arange(100), 26, components=components)


def test_forecast_rejects_unstable_or_invalid_subspaces():
    from src.analysis.ssa import decompose, recurrent_forecast
    result = decompose(np.random.default_rng(3).normal(size=100), 26, components=26)
    for indices, steps in [([], 1), ([26], 1), ([-1], 1), ([0, 0], 1), ([0], 0), ([0], 1.5)]:
        with pytest.raises(ValueError):
            recurrent_forecast(result, indices, steps)
    with pytest.raises(ValueError, match='unstable'):
        recurrent_forecast(result, list(range(26)))
