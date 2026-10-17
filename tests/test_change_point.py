"""Exact finite-grid change-point mathematics, independent of source data."""

import itertools

import numpy as np
import pytest

from src.analysis.change_point import (
    bernoulli_cost, bernoulli_cost_matrix, best_split, boundary_concordance,
    cusum, distribution_distance, gaussian_cost_matrix, segment,
)


def test_bernoulli_cost_known_values_and_zero_terms():
    np.testing.assert_allclose(bernoulli_cost([0, 2, 4], 4), [0, 8*np.log(2), 0])
    assert bernoulli_cost(1, 2) == pytest.approx(4*np.log(2))
    np.testing.assert_allclose(bernoulli_cost([0, 1], [1, 1]), 0)


@pytest.mark.parametrize("counts,length", [([-1], 4), ([5], 4), ([1], 0), ([np.nan], 4), ([1], np.inf)])
def test_bernoulli_rejects_invalid_counts(counts, length):
    with pytest.raises(ValueError):
        bernoulli_cost(counts, length)


def test_bernoulli_cost_matrix_multivariate_and_endpoint_indices():
    x = np.array([[0, 1], [0, 0], [1, 0], [1, 1]])
    costs = bernoulli_cost_matrix(x, [0, 2, 4], per_dimension=True)
    assert costs.shape == (3, 3, 2)
    np.testing.assert_allclose(costs[0, 1], [0, 4*np.log(2)])
    np.testing.assert_allclose(costs[0, 2], [8*np.log(2)]*2)
    np.testing.assert_allclose(bernoulli_cost_matrix(x, [0, 2, 4])[0, 2], 16*np.log(2))
    assert np.isinf(costs[2, 0]).all()
    assert np.isinf(costs[1, 1]).all() or np.all(costs[1, 1] == 0)


@pytest.mark.parametrize("endpoints", [[0, 2, 2, 4], [0, 4, 2], [0, 2.5, 4], [-1, 4], [0, 5]])
def test_cost_matrix_rejects_invalid_endpoints(endpoints):
    with pytest.raises(ValueError):
        bernoulli_cost_matrix(np.zeros((4, 2)), endpoints)


def test_cost_matrix_rejects_nonbinary_and_nonfinite_observations():
    with pytest.raises(ValueError):
        bernoulli_cost_matrix([[0, 0.2], [1, 0]], [0, 2])
    with pytest.raises(ValueError):
        gaussian_cost_matrix([[0, np.nan], [1, 0]], [0, 2])


def _brute_force(costs, endpoints, minimum, penalty):
    candidates = []
    for size in range(len(endpoints)-1):
        for boundaries in itertools.combinations(range(1, len(endpoints)-1), size):
            indices = (0, *boundaries, len(endpoints)-1)
            if any(endpoints[b]-endpoints[a] < minimum for a, b in zip(indices, indices[1:])):
                continue
            value = sum(costs[a, b] for a, b in zip(indices, indices[1:]))
            actual = tuple(endpoints[i] for i in boundaries)
            candidates.append((value+penalty*size, size, actual, value))
    return min(candidates)


@pytest.mark.parametrize("minimum,penalty", [(1, 0), (1, 2), (2, .5), (3, 100)])
def test_batch_dp_matches_all_partitions(minimum, penalty):
    endpoints = np.array([0, 1, 3, 4, 6, 8])
    rng = np.random.default_rng(1901)
    costs = rng.integers(0, 20, size=(6, 6, 3)).astype(float)
    costs[np.tril_indices(6)] = np.inf
    results = segment(costs, endpoints, minimum=minimum, penalty=penalty)
    assert isinstance(results, list) and len(results) == 3
    for unit, result in enumerate(results):
        expected = _brute_force(costs[:, :, unit], endpoints, minimum, penalty)
        assert result["objective"] == pytest.approx(expected[0])
        assert result["boundaries"] == list(expected[2])
        assert result["cost"] == pytest.approx(expected[3])
        assert result["gain"] == pytest.approx(costs[0, -1, unit]-expected[3])
        ends = [0, *result["boundaries"], 8]
        assert result["segments"] == [[a, b] for a, b in zip(ends, ends[1:])]
        assert result["minimum"] == minimum and result["penalty"] == penalty


def test_ties_prefer_fewer_changes_then_earlier_boundary_without_perturbation():
    costs = np.zeros((5, 5))
    assert segment(costs, range(5), minimum=1, penalty=0)[0]["boundaries"] == []
    costs[0, 4] = 10
    assert segment(costs, range(5), minimum=1, penalty=0)[0]["boundaries"] == [1]
    assert segment(costs, range(5), minimum=1, penalty=10)[0]["boundaries"] == []
    assert best_split(costs, range(5), minimum=1)[0]["boundary"] == 1


def test_binary_planted_change_constant_and_penalty_reuse():
    x = np.column_stack([np.r_[np.zeros(52), np.ones(52)], np.zeros(104)])
    costs = bernoulli_cost_matrix(x, [0, 26, 52, 78, 104], per_dimension=True)
    before = costs.copy()
    fitted = segment(costs, [0, 26, 52, 78, 104], minimum=26, penalty=5)
    assert fitted[0]["boundaries"] == [52]
    assert fitted[1]["boundaries"] == []
    assert segment(costs, [0, 26, 52, 78, 104], minimum=52, penalty=200)[0]["boundaries"] == []
    np.testing.assert_array_equal(costs, before)


def test_gaussian_sse_and_planted_mean_change():
    y = np.array([[-2, -1], [-2, 1], [2, -1], [2, 1]], dtype=float)
    costs = gaussian_cost_matrix(y, [0, 2, 4])
    assert costs[0, 1] == pytest.approx(2)
    assert costs[0, 2] == pytest.approx(20)
    fit = segment(costs, [0, 2, 4], minimum=2, penalty=3)[0]
    assert fit["boundaries"] == [2] and fit["cost"] == pytest.approx(4)
    assert fit["gain"] == pytest.approx(16)
    assert np.all(costs[np.triu_indices(3, 1)] >= 0)


def test_split_is_always_a_proposal_even_without_penalized_change():
    costs = bernoulli_cost_matrix(np.zeros((8, 1)), [0, 2, 4, 6, 8])
    assert segment(costs, [0, 2, 4, 6, 8], minimum=2, penalty=1)[0]["boundaries"] == []
    assert best_split(costs, [0, 2, 4, 6, 8], minimum=2) == [{"boundary": 2, "gain": 0., "cost": 0.}]
    assert best_split(costs, [0, 2, 4, 6, 8], minimum=5) == [{"boundary": None, "gain": 0., "cost": 0.}]


def test_split_with_whole_interval_below_minimum_has_no_feasible_proposal():
    assert best_split(np.zeros((2, 2)), [0, 4], minimum=5) == [
        {"boundary": None, "gain": 0., "cost": 0.},
    ]


@pytest.mark.parametrize("penalty", [-1, np.inf, np.nan])
def test_segment_rejects_invalid_penalty(penalty):
    with pytest.raises(ValueError):
        segment(np.zeros((2, 2)), [0, 4], minimum=2, penalty=penalty)


def test_minimum_uses_endpoint_distances_and_requires_valid_whole_segment():
    costs = np.zeros((4, 4))
    costs[0, -1] = 10
    assert segment(costs, [0, 13, 26, 39], minimum=20, penalty=1)[0]["boundaries"] == []
    with pytest.raises(ValueError):
        segment(costs, [0, 13, 26, 39], minimum=40, penalty=1)
    with pytest.raises(ValueError):
        segment(costs, [0, 13, 26, 39], minimum=0, penalty=1)


def test_cusum_matches_reference_and_constant_location():
    x = np.column_stack([[-1., -1., 1., 1.], np.ones(4)])
    result = cusum(x, minimum=1)
    np.testing.assert_allclose(result["curve"][:, 0], [0, -.5, -1, -.5, 0])
    np.testing.assert_allclose(result["score"], [1, 0])
    np.testing.assert_array_equal(result["location"], [2, -1])
    assert result["curve"].shape == (5, 2)
    unavailable = cusum(x, minimum=3)
    np.testing.assert_array_equal(unavailable["location"], [-1, -1])
    np.testing.assert_allclose(unavailable["score"], 0)


def test_cusum_noninteger_constant_columns_and_roundoff_have_no_evidence():
    x = np.tile([np.sqrt(35/12), 1/3, np.pi], (520, 1))
    x[260:, 2] = np.nextafter(np.pi, np.inf)
    result = cusum(x)
    np.testing.assert_array_equal(result["score"], np.zeros(3))
    np.testing.assert_array_equal(result["location"], [-1, -1, -1])
    np.testing.assert_array_equal(result["curve"], np.zeros((521, 3)))


def test_cusum_small_real_variation_remains_scale_invariant():
    x = np.r_[np.zeros(260), np.full(260, 1e-20)][:, None]
    result = cusum(x)
    assert result["score"][0] == pytest.approx(np.sqrt(520)/2)
    assert result["location"][0] == 260


def test_distribution_distances_use_raw_rates_and_normalized_js():
    result = distribution_distance([1, 0], [0, 1])
    assert result == pytest.approx({"l1": 2, "js": np.log(2), "cosine": 0, "max_shift": 1})
    same_direction = distribution_distance([1, 2], [2, 4])
    assert same_direction == pytest.approx({"l1": 3, "js": 0, "cosine": 1, "max_shift": 2})


def test_distribution_normalization_handles_large_finite_mass():
    result = distribution_distance([1e308, 1e308], [1e308, 1e308])
    assert result == pytest.approx({"l1": 0, "js": 0, "cosine": 1, "max_shift": 0})


@pytest.mark.parametrize("a,b", [([0, 0], [1, 0]), ([-1, 2], [1, 2]), ([np.nan], [1]), ([1], [1, 2])])
def test_distance_rejects_invalid_vectors(a, b):
    with pytest.raises(ValueError):
        distribution_distance(a, b)


def test_boundary_concordance_matches_one_to_one_and_empty_is_zero():
    assert boundary_concordance([10, 11], [10], tolerance=1) == {"f1": 2/3, "matches": 1, "count_a": 2, "count_b": 1}
    assert boundary_concordance([14, 10], [12, 16], tolerance=2)["matches"] == 2
    assert boundary_concordance([], [], tolerance=13) == {"f1": 0., "matches": 0, "count_a": 0, "count_b": 0}
    assert boundary_concordance([1], [3], tolerance=1)["f1"] == 0
    with pytest.raises(ValueError):
        boundary_concordance([1], [1], tolerance=-1)
