"""Graph algebra, causal boundaries, and frequency-adjusted relational features."""
import importlib.util

import numpy as np
import pytest


def draws(groups):
    x = np.zeros((len(groups), 45), dtype=bool)
    for row, group in zip(x, groups):
        row[list(group)] = True
    return x


def random_draws(n=104, seed=714):
    rng = np.random.default_rng(seed)
    return draws([rng.choice(45, 6, replace=False) for _ in range(n)])


def test_graph_module_available():
    assert importlib.util.find_spec('src.analysis.graph_structure') is not None


def test_each_draw_contributes_fifteen_pairs_and_strength_is_five_times_frequency():
    from src.analysis.graph_structure import graph
    x = draws([range(6), range(3, 9), range(6)])
    g = graph(x)
    a = g['adjacency']
    assert a.shape == (45, 45) and a.dtype.kind in 'iu'
    np.testing.assert_array_equal(a, a.T)
    assert not np.diag(a).any()
    assert np.triu(a, 1).sum() == 45
    assert a[0, 1] == 2 and a[3, 4] == 3 and a[0, 6] == 0
    np.testing.assert_array_equal(g['frequency'][:9], [2, 2, 2, 3, 3, 3, 1, 1, 1])
    np.testing.assert_array_equal(g['strength'], 5 * g['frequency'])
    np.testing.assert_array_equal(g['binary'], a >= 2)
    assert g['window'] == 3
    assert g['expected_pair'] == pytest.approx(3 / 66)
    assert g['node_expected_strength'] == 2
    assert g['expected_concentration'] == pytest.approx(1 / 990 + (1 - 1 / 66) / 45)
    assert g['concentration'] == pytest.approx(np.square(np.triu(a, 1)).sum() / 45 ** 2)


def test_rolling_window_uses_only_exact_prefix_and_counts_do_not_overflow():
    from src.analysis.graph_structure import graph
    x = random_draws(80)
    g = graph(x[:65], window=26, cutoff=65)
    expected = graph(x[39:65])
    np.testing.assert_array_equal(g['adjacency'], expected['adjacency'])
    assert g['window'] == 26
    dense = graph(draws([range(6)] * 104))
    assert dense['adjacency'][0, 1] == 104
    assert dense['strength'][0] == 520
    for kwargs in ({'cutoff': 64}, {'cutoff': 66}, {'window': 0}, {'window': 66},
                   {'window': True}, {'window': 2.5}, {'threshold': 0}, {'threshold': True}):
        with pytest.raises(ValueError):
            graph(x[:65], **kwargs)
    with pytest.raises(ValueError):
        graph(draws([range(6)] * 1246))
    with pytest.raises(ValueError):
        graph(np.zeros((2, 45)))


def test_clique_motifs_and_common_neighbor_diagonal_are_hand_counted():
    from src.analysis.graph_structure import graph
    g = graph(draws([range(6), range(6, 12)]), window=1, threshold=1)
    assert g['triangles'] == 20
    assert g['wedges'] == 60
    assert g['transitivity'] == 1
    assert g['density'] == pytest.approx(15 / 990)
    np.testing.assert_array_equal(g['degree'][6:12], np.full(6, 5))
    np.testing.assert_array_equal(g['local_clustering'][6:12], np.ones(6))
    assert g['clustering'] == pytest.approx(6 / 45)
    assert g['common_neighbors'][6, 7] == 4
    np.testing.assert_array_equal(g['common_neighbors'].diagonal(), g['degree'])
    empty = graph(draws([range(6), range(6, 12)]))
    assert empty['triangles'] == empty['wedges'] == empty['transitivity'] == 0


def test_frequency_conditioned_expectation_and_residual_orthogonality():
    from src.analysis.graph_structure import graph, freq_edge_expectation, residualize
    g = graph(random_draws())
    f = g['frequency']
    expectation = freq_edge_expectation(f, 104)
    assert expectation[0, 1] == pytest.approx(45 / 44 * 5 / 6 * f[0] * f[1] / 104)
    assert not expectation.diagonal().any()
    np.testing.assert_allclose(g['residual_adjacency'], g['adjacency'] - expectation)
    residual = residualize(np.arange(45.) ** 2, f)
    assert abs(residual.sum()) < 1e-8
    assert abs(residual @ f) < 1e-7
    np.testing.assert_allclose(residualize(g['strength'], f), 0, atol=1e-10)
    np.testing.assert_allclose(residualize(np.ones(45), np.ones(45)), 0, atol=1e-12)
    with pytest.raises(ValueError):
        residualize(np.full(45, np.nan), f)


def test_graph_similarities_use_upper_triangle_and_define_zero_cases():
    from src.analysis.graph_structure import similarity, graph_similarity
    a, b = np.zeros((45, 45)), np.zeros((45, 45))
    a[0, 1] = a[1, 0] = 2
    b[1, 2] = b[2, 1] = 2
    same = similarity(a, a)
    assert same == pytest.approx(dict(cosine=1, correlation=1, frobenius=0, jaccard=1))
    different = similarity(a, b)
    assert different['cosine'] == different['jaccard'] == 0
    assert different['frobenius'] == pytest.approx(4)
    assert different['correlation'] == pytest.approx(-1 / 989)
    zero = np.zeros_like(a)
    assert similarity(zero, zero) == pytest.approx(dict(cosine=1, correlation=1, frobenius=0, jaccard=1))
    assert similarity(a, zero)['cosine'] == similarity(a, zero)['correlation'] == 0
    assert graph_similarity({'adjacency': a}, {'adjacency': b}) == different


@pytest.mark.parametrize('communities', [2, 3])
def test_spectral_partition_recovers_blocks_deterministically_and_marks_isolates(communities):
    from src.analysis.graph_structure import spectral_partition, adjusted_rand
    a = np.zeros((45, 45))
    truth = np.full(45, -1)
    for label in range(communities):
        members = np.arange(label * 12, (label + 1) * 12)
        a[np.ix_(members, members)] = 3
        truth[members] = label
    np.fill_diagonal(a, 0)
    labels = spectral_partition(a, communities)
    np.testing.assert_array_equal(labels, spectral_partition(a, communities))
    assert adjusted_rand(labels, truth) == pytest.approx(1)
    np.testing.assert_array_equal(labels, truth)
    np.testing.assert_array_equal(spectral_partition(np.zeros((45, 45)), communities), -np.ones(45))


def test_adjusted_rand_is_label_invariant_and_uses_only_common_nonisolates():
    from src.analysis.graph_structure import adjusted_rand
    assert adjusted_rand([0, 0, 1, 1, -1], [7, 7, 8, 8, 9]) == 1
    assert adjusted_rand([0, 0, 1, 1], [0, 1, 0, 1]) == pytest.approx(-.5)
    assert adjusted_rand([-1, -1], [-1, 0]) == 0
    assert adjusted_rand([0, 0], [7, 7]) == 1


def test_relational_features_follow_fixed_formulas_then_remove_frequency():
    from src.analysis.graph_structure import graph, relational_features, residualize
    x = random_draws()
    g = graph(x)
    features = relational_features(g, x[-1], communities=2)
    f = g['frequency']
    r = g['residual_adjacency']
    winners = np.flatnonzero(x[-1])
    for i in (0, int(winners[0])):
        others = winners[winners != i]
        expected = np.mean(r[i, others] / np.sqrt((f[i] + 5) * (f[others] + 5)))
        assert features['raw_features']['neighbor'][i] == pytest.approx(expected)
        members = (features['labels'] == features['labels'][i]) & (features['labels'][i] >= 0)
        assert features['raw_features']['community'][i] == pytest.approx(r[i, members].sum() / (5 * f[i] + 5))
    for key in ('neighbor', 'community', 'clustering'):
        v = features[key]
        residual = residualize(features['raw_features'][key], f)
        np.testing.assert_allclose(v, residual / residual.std(), atol=1e-10)
        assert abs(v.mean()) < 1e-10 and abs(v @ f) < 1e-8
        assert v.std() == pytest.approx(1)
    np.testing.assert_array_equal(features['strength_residual'], np.zeros(45))
    # No binary edges: weighted communities still exist; neighbor is linear in f.
    constant = graph(draws([range(6)] * 26), threshold=27)
    output = relational_features(constant, draws([range(6)])[0])
    for key in ('neighbor', 'community', 'clustering'):
        assert np.isfinite(output[key]).all()
    for key in ('neighbor', 'clustering'):
        np.testing.assert_array_equal(output[key], np.zeros(45))
    with pytest.raises(ValueError):
        relational_features(g, np.zeros(45))


def test_relational_community_uses_weighted_graph_even_without_thresholded_edges():
    from src.analysis.graph_structure import graph, relational_features, spectral_partition
    x = random_draws(26)
    g = graph(x, threshold=100)
    assert not g['binary'].any()
    features = relational_features(g, x[-1])
    assert (features['labels'] >= 0).sum() > 20
    np.testing.assert_array_equal(features['labels'], spectral_partition(g['adjacency'], 2))
