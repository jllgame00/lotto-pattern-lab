"""Hand-checked finite-population residue and causal transition contracts."""
import importlib

import numpy as np
import pytest


def modular():
    # Missing-feature failures remain explicit before the module is implemented.
    try:
        return importlib.import_module('src.analysis.modular_space')
    except ModuleNotFoundError:
        pytest.fail('Phase15 modular-space representation is not implemented')


def draws(*rows):
    x = np.zeros((len(rows), 45), dtype=bool)
    for t, row in enumerate(rows):
        x[t, np.asarray(row) - 1] = True
    return x


def test_residue_mapping_keeps_zero_class_and_unequal_populations():
    m = modular()
    x = draws([7, 13, 21, 25, 32, 44], [7, 13, 21, 25, 32, 44])
    out = m.representation(x, 7, cutoff=2)
    np.testing.assert_array_equal(out['histogram'], [[2, 0, 1, 0, 2, 0, 1]] * 2)
    np.testing.assert_array_equal(out['populations'], [6, 7, 7, 7, 6, 6, 6])
    np.testing.assert_allclose(out['expected'], [4/5, 14/15, 14/15, 14/15, 4/5, 4/5, 4/5])
    np.testing.assert_array_equal(out['occupied'], [4, 4])
    np.testing.assert_allclose(out['concentration'], [5/18, 5/18])
    np.testing.assert_allclose(out['entropy'], [np.log2(3) + 1/3] * 2)
    np.testing.assert_array_equal(out['repeats'], [2, 2])
    np.testing.assert_array_equal(out['repeated_classes'], [2, 2])


def test_parity_reference_and_finite_population_covariance():
    m = modular()
    x = draws([7, 13, 21, 25, 32, 44], [2, 4, 6, 8, 10, 12])
    out = m.representation(x, 2)
    np.testing.assert_array_equal(out['histogram'], [[2, 4], [6, 0]])
    np.testing.assert_array_equal(out['populations'], [22, 23])
    v = 6 * 39/44 * 22/45 * 23/45
    np.testing.assert_allclose(out['covariance'], [[v, -v], [-v, v]])
    np.testing.assert_allclose(out['imbalance'][0],
                               [(2 - 44/15)/np.sqrt(v), (4 - 46/15)/np.sqrt(v)])


@pytest.mark.parametrize('k', [2, 3, 4, 5, 6, 7])
def test_balanced_number_frequencies_match_iid_residue_expectation(k):
    m = modular()
    x = draws(*[[(i + j) % 45 + 1 for j in range(6)] for i in range(45)])
    out = m.representation(x, k)
    np.testing.assert_allclose(out['histogram'].mean(axis=0), out['expected'])
    np.testing.assert_allclose(out['imbalance'].mean(axis=0), 0, atol=1e-15)
    np.testing.assert_allclose(out['covariance'].sum(axis=0), 0, atol=1e-15)


def test_lag_alignment_never_wraps_and_returns_independent_arrays():
    m = modular()
    h = np.array([[0, 6], [1, 5], [2, 4], [3, 3], [4, 2]])
    source, future = m.lagged(h, 2)
    np.testing.assert_array_equal(source, [[0, 6], [1, 5], [2, 4]])
    np.testing.assert_array_equal(future, [[2, 4], [3, 3], [4, 2]])
    source[0, 0] = 99
    future[0, 0] = 99
    assert h[0, 0] == 0 and h[2, 0] == 2
    for lag in (0, 5, 6, 27, True, 1.5):
        with pytest.raises(ValueError):
            m.lagged(h, lag)


def test_conditional_transition_uses_aligned_future_and_finite_sample_z():
    m = modular()
    even, odd = [2, 4, 6, 8, 10, 12], [1, 3, 5, 7, 9, 11]
    out = m.transition(draws(*([even, odd] * 30 + [even])), 2, 1)
    np.testing.assert_array_equal(out['counts'], [[30, 0, 0, 0, 0, 0, 30]] * 2)
    np.testing.assert_array_equal(out['sums'], [[180, 0, 0, 0, 0, 0, 0]] * 2)
    np.testing.assert_array_equal(out['conditional_means'][:, [0, 6]], [[6, 0], [6, 0]])
    np.testing.assert_array_equal(out['baseline'], [3, 3])
    np.testing.assert_array_equal(out['variance'], [9, 9])
    np.testing.assert_array_equal(out['eligible'][:, [0, 6]], [[True, True]] * 2)
    assert out['eligible'].sum() == 4
    np.testing.assert_allclose(out['z'][:, [0, 6]], [[np.sqrt(60), -np.sqrt(60)]] * 2)
    assert np.isnan(out['conditional_means'][:, 1:6]).all()
    assert np.isnan(out['z'][:, 1:6]).all()


def test_successor_baseline_excludes_source_only_draw_and_support_is_reselected():
    m = modular()
    even, odd = [2, 4, 6, 8, 10, 12], [1, 3, 5, 7, 9, 11]
    out = m.transition(draws(*([even, odd] * 19 + [even])), 2, 1)
    assert not out['eligible'].any()  # Both observed states have only 19 examples.
    assert np.isnan(out['z']).all()
    out = m.transition(draws(even, odd, odd), 2, 1)
    np.testing.assert_array_equal(out['baseline'], [0, 6])
    np.testing.assert_array_equal(out['variance'], [0, 0])
    assert not out['eligible'].any()
    constant = m.transition(draws(*([even] * 45)), 2, 1)
    assert not constant['eligible'].any()  # n_state == M, and variance is zero.


@pytest.mark.parametrize('cutoff', [1, 3, 1246, True, 2.5])
def test_cutoff_must_equal_input_prefix(cutoff):
    x = draws([1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12])
    with pytest.raises(ValueError):
        modular().representation(x, 3, cutoff=cutoff)


def test_rejects_undeclared_modulus_future_rows_and_nonbinary_draws():
    m = modular()
    x = draws([1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12])
    for k in (1, 8, True, 2.0):
        with pytest.raises(ValueError):
            m.representation(x, k)
    with pytest.raises(ValueError):
        m.representation(np.tile(x[:1], (1246, 1)), 3)
    x = x.astype(float)
    x[0, 0], x[0, 1] = 0.5, 1.5
    with pytest.raises(ValueError):
        m.representation(x, 3)
