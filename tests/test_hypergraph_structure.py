"""Hand-checked subset counts and causal hypergraph contracts."""
import numpy as np
import pytest
from src.analysis.hypergraph_structure import (TRIPLES, PAIRS, binary_hyperedges,
    subset_ids, subset_counts, motif_diagnostic, continuation_scores,
    set_similarity, pairwise_overlap)


def matrix(rows):
    x = np.zeros((len(rows), 45), bool)
    for i, row in enumerate(rows):
        x[i, np.asarray(row) - 1] = True
    return x


def test_twenty_unique_triples_and_ten_times_node_frequency():
    x = matrix([[1, 2, 3, 4, 5, 6], [2, 3, 4, 5, 6, 7]])
    ids = subset_ids(x)
    assert ids.shape == (2, 20)
    assert len(np.unique(ids[0])) == 20
    assert tuple(TRIPLES[ids[0, 0]]) == (0, 1, 2)
    assert tuple(TRIPLES[ids[1, -1]]) == (4, 5, 6)
    result = subset_counts(x)
    assert result['counts'].sum() == 40
    assert result['counts'][0] == 1
    np.testing.assert_array_equal(result['node_participation'], 10 * x.sum(0))
    assert result['expected'] == pytest.approx(40 / 14190)
    assert result['lift'][0] == pytest.approx(14190 / 40)
    assert len(TRIPLES) == 14190 and len(PAIRS) == 990
    np.testing.assert_array_equal(binary_hyperedges(x), [[1,2,3,4,5,6], [2,3,4,5,6,7]])


def test_window_counts_and_absolute_recurrence_intervals():
    x = matrix([[1,2,3,4,5,6], [7,8,9,10,11,12], [1,2,3,13,14,15],
                [16,17,18,19,20,21], [1,2,3,22,23,24]])
    d = motif_diagnostic(x, [1,2,3], window=3)
    assert d['occurrences'] == [3, 5]
    assert d['recurrence_intervals'] == [2]
    assert d['count'] == 2 and d['recent_count'] == 2 and d['longterm_count'] == 1
    assert d['window'] == 3
    assert d['expected'] == pytest.approx(60 / 14190)
    assert d['trend'] == pytest.approx(2/3 - 1/2)
    previous = motif_diagnostic(x[:3], [1,2,3], cutoff=3, window=2)
    assert previous['occurrences'] == [3]
    counts = subset_counts(x[:3], cutoff=3, window=2)
    assert counts['counts'][0] == 1 and counts['counts'].sum() == 40
    assert subset_ids(x, size=2).shape == (5,15)


def test_supported_conditional_continuation_finds_planted_triple_without_self_context():
    x = matrix([[1,2,3,10,11,12], [1,2,3,13,14,15], [1,2,3,16,17,18],
                [4,5,6,7,8,9], [1,2,20,21,22,23]])
    result = continuation_scores(x, window=5, support=2, shrinkage=5)
    three = result['diagnostics'][2]
    assert three['number'] == 3 and three['own_frequency'] == 3
    assert len(three['contexts']) == 1
    context = three['contexts'][0]
    assert context['pair'] == [1, 2] and context['c_pair'] == 4 and context['c_triple'] == 3
    assert context['conditional'] == pytest.approx(2/3)
    assert context['weight'] == pytest.approx(4/9)
    assert result['raw_scores'][2] == pytest.approx((2/3 - 3/5) * 4/9)
    for item in result['diagnostics']:
        assert all(item['number'] not in context['pair'] for context in item['contexts'])
    assert np.array_equal(result['raw_scores'], continuation_scores(x,5,2,5)['raw_scores'])


def test_sparse_triples_fall_back_to_neutral_and_counts_are_prefix_causal():
    x = matrix([[1,2,3,4,5,6], [7,8,9,10,11,12], [13,14,15,16,17,18]])
    assert np.all(continuation_scores(x,3)['raw_scores'] == 0)
    future = np.vstack((x, matrix([[1,2,3,20,21,22]])))
    with pytest.raises(ValueError):
        subset_counts(future,cutoff=3)
    np.testing.assert_array_equal(subset_counts(x,cutoff=3)['counts'], subset_counts(x)['counts'])


def test_overlap_three_is_jaccard_one_third_and_pairwise_counts_are_integer():
    rows = [[1,2,3,4,5,6], [1,2,3,7,8,9]]
    assert set_similarity(*rows) == {'overlap': 3, 'jaccard': 1/3}
    pairwise = pairwise_overlap(matrix(rows))
    np.testing.assert_array_equal(pairwise['overlap'], [[6,3],[3,6]])
    np.testing.assert_allclose(pairwise['jaccard'], [[1,1/3],[1/3,1]])


@pytest.mark.parametrize('call', [
    lambda x: subset_counts(x,window=4), lambda x: subset_counts(x,cutoff=4),
    lambda x: subset_counts(x,size=4), lambda x: subset_counts(x,window=True),
    lambda x: motif_diagnostic(x,[3,2,1]), lambda x: motif_diagnostic(x,[1,1,2]),
    lambda x: continuation_scores(x,3,support=1),
    lambda x: continuation_scores(x,3,shrinkage=0)])
def test_invalid_windows_subsets_and_feature_settings_rejected(call):
    x = matrix([[1,2,3,4,5,6]] * 3)
    with pytest.raises(ValueError):
        call(x)


def test_invalid_and_future_input_rejected_even_with_earlier_cutoff():
    for x in [np.ones((3,45)), np.zeros((3,44)), matrix([[1,2,3,4,5,6]]*1246)]:
        with pytest.raises(ValueError):
            binary_hyperedges(x, cutoff=2)
    with pytest.raises(ValueError):
        set_similarity([1,1,2,3,4,5], [1,2,3,4,5,6])
