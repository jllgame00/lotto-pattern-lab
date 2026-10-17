"""Exact distance geometry, finite-population opportunities and causal shapes."""
from math import comb

import numpy as np
import pytest


def matrix(*draws):
    x = np.zeros((len(draws), 45), dtype=bool)
    for row, draw in enumerate(draws):
        x[row, np.asarray(draw) - 1] = True
    return x


def test_representation_keeps_all_fifteen_nonwrapping_pairs_and_anchor():
    from src.analysis.difference_space import representation

    x = matrix([1, 2, 4, 8, 16, 45], [2, 3, 5, 9, 17, 44])
    result = representation(x, cutoff=2)
    assert result['sorted_numbers'][0].tolist() == [1, 2, 4, 8, 16, 45]
    assert result['gaps'][0].tolist() == [1, 2, 4, 8, 29]
    assert result['pairwise'][0].tolist() == [1, 3, 7, 15, 44, 2, 6, 14, 43, 4, 12, 41, 8, 37, 29]
    assert result['anchored'][0].tolist() == [0, 1, 3, 7, 15, 44]
    np.testing.assert_allclose(result['normalized_gaps'][0], np.array([1, 2, 4, 8, 29]) / 44)
    assert result['pair_histogram'][0, 43] == 1
    assert result['pair_histogram'].sum(axis=1).tolist() == [15, 15]
    assert result['adjacent_histogram'].sum(axis=1).tolist() == [5, 5]
    np.testing.assert_allclose(result['gap_entropy'][0], 1.484853235485034)


def test_within_draw_expectations_count_unordered_pairs_and_adjacent_gaps():
    from src.analysis.difference_space import representation

    result = representation(matrix(range(1, 7), range(2, 8)))
    assert result['opportunities'].tolist() == list(range(44, 0, -1))
    assert result['pair_expected'][0] == pytest.approx(2 / 3)
    assert result['pair_expected'][-1] == pytest.approx(1 / 66)
    assert result['adjacent_expected'][0] == pytest.approx(2 / 3)
    assert result['adjacent_expected'][39] == pytest.approx(5 / comb(45, 6))
    assert not result['adjacent_expected'][40:].any()
    assert result['pair_expected'].sum() == pytest.approx(15)
    assert result['adjacent_expected'].sum() == pytest.approx(5)


def test_representation_entropy_of_equal_spacing_is_log2_five():
    from src.analysis.difference_space import representation

    result = representation(matrix([1, 3, 5, 7, 9, 11], [11, 13, 15, 17, 19, 21]))
    np.testing.assert_allclose(result['normalized_gaps'], .2)
    np.testing.assert_allclose(result['gap_entropy'], np.log2(5))


def test_research_guards_exact_cutoff_binary_six_and_no_future_draw():
    from src.analysis.difference_space import representation

    x = matrix(range(1, 7), range(2, 8))
    for bad in (x[:, :44], np.zeros((2, 45)), np.tile(x[:1], (1246, 1))):
        with pytest.raises(ValueError):
            representation(bad)
    with pytest.raises(ValueError):
        representation(x, cutoff=1)
    with pytest.raises(ValueError):
        representation(x, cutoff=True)


def test_absolute_relation_hand_checked_boundary_opportunities_and_variance():
    from src.analysis.difference_space import absolute_relation

    result = absolute_relation(matrix(range(1, 7), range(2, 8)), lag=1)
    assert result['observed'][[0, 1, 44]].tolist() == [5, 10, 0]
    assert result['opportunity'][[0, 1, 44]].tolist() == [6, 11, 1]
    assert result['expected'][[0, 1, 44]].tolist() == pytest.approx([.8, 22 / 15, 2 / 15])
    variance = 6 * 39 / 44 * (19 / 45 - (11 / 45) ** 2)
    assert result['var'][1] == pytest.approx(variance)
    assert result['z'][1] == pytest.approx((10 - 22 / 15) / np.sqrt(variance))
    assert result['source_counts'].tolist() == [1] * 6 + [0] * 39
    np.testing.assert_array_equal(result['support'], result['observed'])
    assert result['observed'].sum() == 36
    assert result['opportunity'].sum() == 270


def test_absolute_relation_lag_is_directional_and_never_wraps():
    from src.analysis.difference_space import absolute_relation

    draws = [[1, 4, 8, 13, 21, 45], [2, 6, 12, 23, 31, 40], [3, 7, 15, 20, 29, 44]]
    result = absolute_relation(matrix(*draws), lag=2)
    expected_counts = [sum(abs(a - b) == d for a in draws[0] for b in draws[2]) for d in range(45)]
    assert result['observed'].tolist() == expected_counts
    assert result['observed'].sum() == 36
    for lag in (0, True, 5, 3):
        with pytest.raises(ValueError):
            absolute_relation(matrix(*draws), lag=lag)


def test_temporal_distance_recovers_planted_distance_one_transition():
    from src.analysis.difference_space import absolute_relation

    rng = np.random.default_rng(150042)
    sources = [rng.choice(np.arange(1, 44, 2), 6, replace=False) for _ in range(200)]
    draws = [draw for source in sources for draw in (source, source + 1)]
    result = absolute_relation(matrix(*draws), lag=1)
    assert result['z'][1] > 10
    assert result['z'][1] > result['z'][43]


def test_shape_distance_is_euclidean_in_normalized_gap_space():
    from src.analysis.difference_space import shape_distance

    a = np.array([.2, .2, .2, .2, .2])
    b = np.array([.1, .3, .2, .2, .2])
    assert shape_distance(a, b) == pytest.approx(np.sqrt(.02))
    np.testing.assert_allclose(shape_distance(np.array([a, b]), np.array([b])), [[np.sqrt(.02)], [0]])
    with pytest.raises(ValueError):
        shape_distance(np.ones(6), np.ones(6))


def test_shape_neighbors_obey_theiler_boundary_and_stable_ties():
    from src.analysis.difference_space import shape_successor

    spaced = [1, 3, 5, 7, 9, 11]
    alternate = [1, 2, 3, 4, 5, 45]
    draws = [alternate] * 77 + [spaced] * 44
    result = shape_successor(matrix(*draws), K=10, endpoints=(104,))
    row = result['rows'][0]
    assert row['endpoint'] == 104
    assert row['target_draw'] == 105
    assert row['neighbor_draws'] == [78, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert max(row['neighbor_draws']) <= 78
    assert row['nearest_distance'] < row['baseline_distance']
    assert result['predictions'].shape == (1, 5)
    assert result['score'] == 0
    changed = matrix(*draws)
    changed[105:] = matrix(*([alternate] * (len(changed) - 105)))
    other = shape_successor(changed, K=10, endpoints=(104,))
    np.testing.assert_array_equal(result['predictions'], other['predictions'])
    np.testing.assert_array_equal(result['baseline_predictions'], other['baseline_predictions'])


def test_shape_score_is_paired_gain_t_and_uses_fixed_query_grid():
    from src.analysis.difference_space import shape_successor

    rng = np.random.default_rng(123)
    x = matrix(*(rng.choice(np.arange(1, 46), 6, replace=False) for _ in range(161)))
    result = shape_successor(x, K=25)
    assert [r['endpoint'] for r in result['rows']] == [104, 130, 156, 160]
    gains = np.array([r['mse_baseline'] - r['mse_model'] for r in result['rows']])
    assert result['score'] == pytest.approx(gains.mean() / (gains.std(ddof=1) / np.sqrt(4)))
    for row, pred, actual in zip(result['rows'], result['predictions'], result['actual']):
        assert row['mse_model'] == pytest.approx(np.mean((pred - actual) ** 2))
        assert row['K'] == 25
    with pytest.raises(ValueError):
        shape_successor(x, K=11)
    with pytest.raises(ValueError):
        shape_successor(x, K=25, endpoints=(len(x),))


def test_shape_constant_history_has_exact_zero_gain_and_zero_score():
    from src.analysis.difference_space import shape_successor

    x = matrix(*([[1, 3, 5, 7, 9, 11]] * 161))
    result = shape_successor(x, K=10)
    assert not result['gains'].any()
    assert result['score'] == 0
    assert all(row['mse_model'] == row['mse_baseline'] == 0 for row in result['rows'])


def test_shape_short_history_has_explicit_empty_diagnostic():
    from src.analysis.difference_space import shape_successor

    result = shape_successor(matrix(range(1, 7), range(2, 8)), K=25)
    assert result['rows'] == []
    assert result['score'] == 0
    assert result['predictions'].shape == result['actual'].shape == (0, 5)
