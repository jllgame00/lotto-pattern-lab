"""Independent fixtures for the Phase 13 discrete information estimators."""
import importlib.util
import itertools

import numpy as np
import pytest


def test_information_module_exists():
    assert importlib.util.find_spec('src.analysis.information') is not None


def test_discrete_mi_exact_independence_dependence_and_constants():
    from src.analysis.information import discrete_mi
    assert discrete_mi([0, 0, 1, 1], [0, 1, 0, 1]) == pytest.approx(0)
    assert discrete_mi([0, 0, 1, 1], [0, 0, 1, 1]) == pytest.approx(1)
    assert discrete_mi([7, 7, 8, 8], ['a', 'a', 'b', 'b']) == pytest.approx(1)
    assert discrete_mi([0, 0, 0, 0], [0, 1, 0, 1]) == 0


def test_conditional_mi_xor_and_conditional_independence():
    from src.analysis.information import conditional_mi
    assert conditional_mi([0, 0, 1, 1], [0, 1, 1, 0], [0, 1, 0, 1]) == pytest.approx(1)
    assert conditional_mi([0, 0, 1, 1], [0, 0, 1, 1], [0, 0, 1, 1]) == pytest.approx(0)


@pytest.mark.parametrize('args', [([], []), ([1, 2], [1]), ([[0, 1]], [1]), ([0, np.nan], [0, 1])])
def test_scalar_mi_rejects_invalid_observations(args):
    from src.analysis.information import discrete_mi
    with pytest.raises(ValueError):
        discrete_mi(*args)


def test_lagged_states_use_original_target_history_without_wraparound():
    from src.analysis.information import lagged_states
    x = np.array([[0], [1], [1], [0], [1], [0]], dtype=int)
    source = 1 - x
    states = lagged_states(x, lag=2, k=2, l=2, source=source)
    assert states['start'] == 3
    np.testing.assert_array_equal(states['source'][:, 0], [2, 0, 1])
    np.testing.assert_array_equal(states['past'][:, 0], [3, 2, 1])
    np.testing.assert_array_equal(states['future'][:, 0], [0, 1, 0])


@pytest.mark.parametrize('kwargs', [dict(lag=0), dict(lag=-1), dict(lag=1.5), dict(lag=True), dict(k=0), dict(k=3), dict(l=0), dict(l=3)])
def test_lagged_states_reject_invalid_history_parameters(kwargs):
    from src.analysis.information import lagged_states
    params = dict(lag=1, k=1, l=1)
    params.update(kwargs)
    with pytest.raises(ValueError):
        lagged_states(np.zeros((8, 2)), **params)


@pytest.mark.parametrize('x', [np.zeros(10), np.zeros((0, 2)), np.zeros((5, 0)), [[0, 2], [1, 0]], [[0, np.nan], [1, 0]]])
def test_lagged_states_reject_nonbinary_or_malformed_matrices(x):
    from src.analysis.information import lagged_states
    with pytest.raises(ValueError):
        lagged_states(x, 1, 1, 1)


def test_lagged_states_reject_insufficient_history_and_wrong_source_shape():
    from src.analysis.information import lagged_states
    with pytest.raises(ValueError, match='history'):
        lagged_states(np.zeros((2, 3)), 2, 1, 1)
    with pytest.raises(ValueError, match='shape'):
        lagged_states(np.zeros((8, 3)), 1, 1, 1, source=np.zeros((8, 2)))


def _dense_information(counts):
    """Reference sum of log probability ratios, independent of entropy code."""
    n = counts.sum()
    if counts.ndim == 2:
        a = counts.sum(axis=1)
        b = counts.sum(axis=0)
        return sum(c / n * np.log2(c * n / (a[i] * b[j]))
                   for (i, j), c in np.ndenumerate(counts) if c)
    xz = counts.sum(axis=2)
    zy = counts.sum(axis=0)
    z = counts.sum(axis=(0, 2))
    return sum(c / n * np.log2(c * z[j] / (xz[i, j] * zy[j, h]))
               for (i, j, h), c in np.ndenumerate(counts) if c)


def _mm_delta(counts):
    occupied = lambda a: np.count_nonzero(a)
    n = counts.sum()
    if counts.ndim == 2:
        delta = occupied(counts.sum(1)) + occupied(counts.sum(0)) - occupied(counts) - 1
    else:
        delta = (occupied(counts.sum(2)) + occupied(counts.sum(0))
                 - occupied(counts.sum((0, 2))) - occupied(counts))
    return delta / (2 * n * np.log(2))


def test_mi_pair_axes_counts_entropies_and_miller_madow_agree_with_dense_reference():
    from src.analysis.information import mi_matrix
    rng = np.random.default_rng(118)
    x = rng.integers(0, 2, size=(317, 3))
    source = rng.integers(0, 2, size=x.shape)
    result = mi_matrix(x, 3, source=source)
    assert result['counts'].shape == (3, 3, 2, 2)
    assert result['samples'] == 314
    assert result['counts'].dtype.kind in 'iu'
    for i, j in itertools.product(range(3), repeat=2):
        expected = np.zeros((2, 2), dtype=int)
        for t in range(3, len(x)):
            expected[source[t - 3, i], x[t, j]] += 1
        np.testing.assert_array_equal(result['counts'][i, j], expected)
        assert result['raw'][i, j] == pytest.approx(_dense_information(expected), abs=1e-14)
        assert result['corrected'][i, j] == pytest.approx(_dense_information(expected) + _mm_delta(expected), abs=1e-14)
    assert result['eligible'].all()
    assert not result['sparse'].any()
    np.testing.assert_array_equal(result['occupied'], np.full((3, 3), 4))
    np.testing.assert_array_equal(result['source_counts'], result['counts'][:, 0].sum(2))
    np.testing.assert_array_equal(result['future_counts'], result['counts'][0].sum(1))


@pytest.mark.parametrize('k,l', [(1, 1), (1, 2), (2, 1), (2, 2)])
def test_te_all_histories_match_dense_tables_and_occupied_mm(k, l):
    from src.analysis.information import te_matrix
    rng = np.random.default_rng(401 + k + l)
    x = rng.integers(0, 2, size=(500, 3))
    source = rng.integers(0, 2, size=x.shape)
    result = te_matrix(x, 4, k, l, source=source)
    start = max(4 + l - 1, k)
    assert result['samples'] == len(x) - start
    assert result['counts'].shape == (3, 3, 2 ** l, 2 ** k, 2)
    for i, j in itertools.product(range(3), repeat=2):
        expected = np.zeros((2 ** l, 2 ** k, 2), dtype=int)
        for t in range(start, len(x)):
            s = sum(2 ** r * source[t - 4 - r, i] for r in range(l))
            z = sum(2 ** r * x[t - 1 - r, j] for r in range(k))
            expected[s, z, x[t, j]] += 1
        np.testing.assert_array_equal(result['counts'][i, j], expected)
        assert result['raw'][i, j] == pytest.approx(_dense_information(expected), abs=1e-14)
        assert result['corrected'][i, j] == pytest.approx(_dense_information(expected) + _mm_delta(expected), abs=1e-14)
    np.testing.assert_array_equal(result['source_past_counts'], result['counts'].sum(4))
    np.testing.assert_array_equal(result['past_future_counts'], result['counts'][0].sum(1))
    np.testing.assert_array_equal(result['source_counts'], result['counts'][:, 0].sum((2, 3)))
    np.testing.assert_array_equal(result['past_counts'], result['counts'][0].sum((1, 3)))
    np.testing.assert_array_equal(result['future_counts'], result['counts'][0].sum((1, 2)))


def test_corrected_mi_retains_negative_estimate_for_exact_independence():
    from src.analysis.information import mi_matrix
    x = np.array([[0], [0], [1], [1], [0]])
    source = np.array([[0], [1], [0], [1], [0]])
    result = mi_matrix(x, 1, source=source, min_samples=1, min_events=1)
    assert result['raw'][0, 0] == pytest.approx(0)
    assert result['corrected'][0, 0] == pytest.approx(-1 / (8 * np.log(2)))


def test_support_rules_keep_zero_cells_and_distinguish_sparse_from_eligibility():
    from src.analysis.information import mi_matrix, te_matrix
    x = np.zeros((401, 2), dtype=int)
    x[:, 1] = np.arange(401) % 2
    mi = mi_matrix(x, 1)
    assert mi['samples'] == 400
    assert mi['sparse'].all()
    assert mi['eligible'][1, 1] and not mi['eligible'][0].any()
    assert not mi['eligible'][:, 0].any()
    np.testing.assert_array_equal(mi['occupied'], [[1, 2], [2, 2]])
    te = te_matrix(x, 1, 2, 2)
    assert not te['eligible'].any()  # Alternation never visits 00 or 11 histories.
    assert np.all(te['counts'].sum((2, 3, 4)) == 399)
    assert not mi_matrix(x[:300], 1)['eligible'].any()


def test_sparse_flags_rare_positive_joint_cells_even_with_full_support():
    from src.analysis.information import mi_matrix
    source = np.array([[0]] * 101 + [[1]] * 101 + [[0]])
    x = np.array([[0]] + [[0]] * 100 + [[1]] + [[0]] + [[1]] * 100)
    result = mi_matrix(x, 1, source=source, min_samples=1, min_events=1)
    np.testing.assert_array_equal(result['counts'][0, 0], [[100, 1], [1, 100]])
    assert result['occupied'][0, 0] == 4
    assert result['sparse'][0, 0]


def test_planted_directional_transfer_and_independent_sources():
    from src.analysis.information import te_matrix
    rng = np.random.default_rng(681)
    x = rng.integers(0, 2, size=(12000, 3))
    x[1:, 1] = x[:-1, 0]
    result = te_matrix(x, 1, 1, 1)
    assert result['raw'][0, 1] > .99
    assert result['raw'][1, 0] < .001
    assert result['raw'][2, 1] < .001
    assert result['eligible'].all()


def test_zero_matrix_has_finite_zero_information_and_ineligible_pairs():
    from src.analysis.information import mi_matrix, te_matrix
    for result in (mi_matrix(np.zeros((320, 3)), 1), te_matrix(np.zeros((320, 3)), 1, 2, 2)):
        np.testing.assert_array_equal(result['raw'], np.zeros((3, 3)))
        np.testing.assert_array_equal(result['corrected'], np.zeros((3, 3)))
        assert not result['eligible'].any()
        assert result['sparse'].all()


def test_exact_sample_event_and_history_support_boundaries():
    from src.analysis.information import mi_matrix,te_matrix
    x=(np.arange(321)%2)[:,None]
    assert not mi_matrix(x[:300],1)['eligible'][0,0]  #299 aligned observations
    assert mi_matrix(x[:301],1)['eligible'][0,0]       #300 aligned observations
    for events in (19,20):
        source=np.zeros_like(x);source[:events]=1
        assert bool(mi_matrix(x,1,source=source)['eligible'][0,0])==(events==20)
    for support in (7,8):
        source=np.zeros_like(x);source[:support]=1
        assert bool(te_matrix(x,1,1,1,source=source)['eligible'][0,0])==(support==8)
