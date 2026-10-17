"""Phase 18 reflection statistics on synthetic six-number draws only."""
import importlib.util
from math import comb

import numpy as np
import pytest


def history(length=208, seed=18):
    rng = np.random.default_rng(seed)
    x = np.zeros((length, 45), dtype=np.uint8)
    for row in x:
        row[rng.choice(45, 6, replace=False)] = 1
    return x


def rows(*numbers):
    x = np.zeros((len(numbers), 45), dtype=np.uint8)
    for row, values in zip(x, numbers):
        row[np.array(values) - 1] = 1
    return x


def test_symmetry_module_exists():
    assert importlib.util.find_spec('src.analysis.symmetry') is not None


def test_mirror_all_45_exact_integers_and_involution():
    from src.analysis.symmetry import mirror
    numbers = np.arange(1, 46)
    np.testing.assert_array_equal(mirror(numbers), np.arange(45, 0, -1))
    np.testing.assert_array_equal(mirror(mirror(numbers)), numbers)
    assert mirror(1) == 45 and mirror(23) == 23 and mirror(45) == 1
    assert isinstance(mirror(np.int64(1)), int)
    for invalid in [0, 46, -1, 1.0, True, [1, 2.0], [1, 46], [True]]:
        with pytest.raises(ValueError):
            mirror(invalid)


def test_shift_has_boundaries_without_wrapping_or_clipping():
    from src.analysis.symmetry import reflection_shift
    assert reflection_shift(1, 0) == 45
    assert reflection_shift(1, 4) is None
    assert reflection_shift(45, -4) is None
    assert reflection_shift(5, 4) == 45
    assert reflection_shift(25, 4) == 25
    for number, shift in [(0, 0), (46, 0), (1.0, 0), (True, 0), (1, 1), (1, 2.0)]:
        with pytest.raises(ValueError):
            reflection_shift(number, shift)


def test_draw_metrics_separate_center_and_normalize_nontrivial_pairs():
    from src.analysis.symmetry import draw_metrics
    x = rows([1, 2, 3, 43, 44, 45], [1, 2, 3, 4, 5, 23], [1, 2, 3, 4, 23, 45])
    result = draw_metrics(x)
    for name, expected in {'pairs': [3, 0, 1], 'paired_numbers': [6, 0, 2],
                           'center': [0, 1, 1], 'left': [3, 5, 4],
                           'right': [3, 0, 1], 'imbalance': [0, 5, 3]}.items():
        np.testing.assert_array_equal(result[name], expected)
    np.testing.assert_allclose(result['symmetry'], [1, 0, .4])
    np.testing.assert_allclose(result['jaccard'], [1, 1/11, 1/3])


def test_exact_joint_distribution_total_mass_and_expected_pairs():
    from src.analysis.symmetry import exact_distribution
    distribution = exact_distribution()
    assert sum(r['probability'] for r in distribution) == pytest.approx(1)
    assert sum(r['pairs'] * r['probability'] for r in distribution) == pytest.approx(1/3)
    assert sum(r['center'] * r['probability'] for r in distribution) == pytest.approx(6/45)
    indexed = {(r['pairs'], r['center']): r['probability'] for r in distribution}
    assert indexed[3, 0] == pytest.approx(comb(22, 3) / comb(45, 6))
    assert indexed[2, 1] == pytest.approx(comb(22, 2) * 20 * 2 / comb(45, 6))


def test_pooled_conditional_lag_zero_and_positive_alignment():
    from src.analysis.symmetry import pooled_relation
    x = rows([1, 2, 3, 4, 5, 23], [1, 2, 3, 4, 23, 45], [1, 2, 3, 43, 44, 45])
    zero, one = pooled_relation(x, 0), pooled_relation(x, 1)
    assert (zero['sources'], zero['hits'], zero['sample_count']) == (16, 8, 3)
    assert zero['rate'] == .5
    assert zero['expected_rate'] == pytest.approx(5/44)
    assert zero['working_z'] == pytest.approx((8-16*5/44) / np.sqrt(16*5/44*39/44))
    assert (one['sources'], one['hits'], one['sample_count']) == (10, 5, 2)
    assert one['expected_rate'] == pytest.approx(6/45)
    assert one['risk_difference'] == pytest.approx(.5-6/45)
    assert one['lift'] == pytest.approx(3.75)
    np.testing.assert_array_equal(one['event_counts'], [5, 5])
    np.testing.assert_array_equal(one['hit_counts'], [1, 4])


def test_shift_pool_excludes_center_fixed_point_and_invalid_mappings():
    from src.analysis.symmetry import pooled_relation
    x = rows([1, 2, 3, 4, 23, 25], [1, 2, 3, 4, 23, 25])
    result = pooled_relation(x, 0, shift=4)
    assert result['sources'] == 0
    assert result['hits'] == 0
    assert np.isnan(result['rate']) and np.isnan(result['working_z'])


def test_pair_order_support_directional_rates_and_aligned_target_baseline():
    from src.analysis.symmetry import pair_relations
    x = rows([1, 2, 3, 4, 5, 23], [1, 2, 3, 4, 23, 45], [1, 2, 3, 43, 44, 45])
    zero = pair_relations(x, 0, minimum_support=2)
    np.testing.assert_array_equal(zero['source'][:4], [1, 45, 2, 44])
    np.testing.assert_array_equal(zero['target'][:4], [45, 1, 44, 2])
    np.testing.assert_array_equal(zero['support'][:2], [3, 2])
    np.testing.assert_allclose(zero['rate'][:2], [2/3, 1])
    np.testing.assert_allclose(zero['baseline'], 5/44)
    assert zero['eligible'][0] and not zero['eligible'][3]
    positive = pair_relations(x, 1, minimum_support=2)
    np.testing.assert_array_equal(positive['support'][:2], [2, 1])
    np.testing.assert_array_equal(positive['hits'][:2], [2, 1])
    assert positive['baseline'][0] == 1
    assert positive['baseline'][2] == .5
    assert not np.any(positive['source'] == 23)


def test_activity_uses_exact_supplied_prefix_and_latest_completed_window():
    from src.analysis.symmetry import activity
    x = history(100)
    result = activity(x[:60], 26, cutoff=60)
    np.testing.assert_allclose(result['own'], x[34:60].mean(axis=0))
    np.testing.assert_allclose(result['mirror'], x[34:60].mean(axis=0)[::-1])
    np.testing.assert_allclose(result['difference'], result['mirror']-result['own'])
    np.testing.assert_allclose(result['sum'], result['own']+result['mirror'])
    with pytest.raises(ValueError):
        activity(x, 26, cutoff=60)
    with pytest.raises(ValueError):
        activity(x[:5], 10)


def test_activity_correlations_align_rolling_endpoints_causally():
    from src.analysis.symmetry import activity_correlations
    x = history(150)
    result = activity_correlations(x)
    assert len(result) == 1122
    row = next(r for r in result if r['window'] == 10 and r['lag'] == 2
               and r['low'] == 1 and r['direction'] == 'low_to_high')
    rates = np.array([x[end-10:end].mean(axis=0) for end in range(10, 151)])
    assert row['samples'] == 139
    assert row['correlation'] == pytest.approx(np.corrcoef(rates[:-2, 0], rates[2:, 44])[0, 1])
    assert row['eligible']
    assert all(r['direction'] == 'low_to_high' for r in result if r['lag'] == 0)
    constant = np.tile(rows([1, 2, 3, 4, 5, 6]), (40, 1))
    assert all(not r['eligible'] and np.isnan(r['correlation']) for r in activity_correlations(constant))


def test_rolling_symmetry_endpoints_and_binary_pair_correlations():
    from src.analysis.symmetry import rolling_symmetry
    x = history(208)
    result = rolling_symmetry(x)
    assert [r['endpoint'] for r in result if r['window'] == 104] == [104, 130, 156, 182, 208]
    final = next(r for r in result if r['window'] == 26 and r['endpoint'] == 208)
    data = x[-26:]
    expected = [np.corrcoef(data[:, low], data[:, 44-low])[0, 1] for low in range(22)
                if data[:, low].std() and data[:, 44-low].std()]
    assert final['valid_pairs'] == len(expected)
    assert final['mean_correlation'] == pytest.approx(np.mean(expected))
    assert final['mean_pairs'] == pytest.approx(sum(len(set(np.flatnonzero(row)) & set(44-np.flatnonzero(row)))
                                                   - int(row[22]) for row in data)/52)
    constant = np.tile(rows([1, 2, 3, 4, 5, 6]), (104, 1))
    assert all(np.isnan(r['mean_correlation']) and r['valid_pairs'] == 0 for r in rolling_symmetry(constant))


def test_planted_lag_one_reflections_detect_temporal_signal():
    from src.analysis.symmetry import pooled_relation
    x = history(600)
    x[1::2] = x[::2, ::-1]
    assert np.all(x.sum(axis=1) == 6)
    assert pooled_relation(x, 1)['rate'] > .5
    assert pooled_relation(x, 1)['rate'] > pooled_relation(x, 2)['rate'] + .3


def test_activity_correlation_needs_26_completed_aligned_rates():
    from src.analysis.symmetry import activity_correlations
    short, enough = activity_correlations(history(34)), activity_correlations(history(35))
    cell = lambda result: next(r for r in result if r['window'] == 10
                               and r['lag'] == 0 and r['pair'] == 1)
    assert cell(short)['samples'] == 25
    assert np.isnan(cell(short)['correlation']) and not cell(short)['eligible']
    assert cell(enough)['samples'] == 26 and cell(enough)['eligible']


def test_regime_correlation_needs_twelve_variable_pairs():
    from src.analysis.symmetry import rolling_symmetry
    rng = np.random.default_rng(19)
    x = np.zeros((104, 45), dtype=np.uint8)
    # Eleven variable pairs, with the other eleven pairs identically absent.
    available = np.r_[np.arange(11), np.arange(34, 45)]
    for row in x:
        row[rng.choice(available, 6, replace=False)] = 1
    for row in rolling_symmetry(x):
        assert row['valid_pairs'] == 11
        assert np.isnan(row['mean_correlation'])


def test_center_never_contributes_to_pooled_source_events_at_positive_lag():
    from src.analysis.symmetry import pooled_relation
    x = rows([1, 2, 3, 4, 5, 23], [6, 7, 8, 9, 10, 23])
    result = pooled_relation(x, 1)
    assert result['sources'] == 5 and result['hits'] == 0
    assert result['rate'] == 0


def test_mixed_boolean_source_labels_do_not_become_integer_numbers():
    from src.analysis.symmetry import mirror
    with pytest.raises(ValueError):
        mirror([1, True])


@pytest.mark.parametrize('lag', [-1, 5, 53, 1.0, True])
def test_unregistered_lags_are_rejected(lag):
    from src.analysis.symmetry import pooled_relation, pair_relations
    for function in [pooled_relation, pair_relations]:
        with pytest.raises(ValueError):
            function(history(), lag)


def test_validation_preserves_research_row_limit_and_six_main_numbers():
    from src.analysis.symmetry import draw_metrics, activity, pooled_relation, rolling_symmetry
    for x in [np.ones((2, 45)), history(1246), history(1), np.zeros((2, 44))]:
        with pytest.raises(ValueError):
            draw_metrics(x)
    for window in [0, 9, 10.0, True]:
        with pytest.raises(ValueError):
            activity(history(), window)
    with pytest.raises(ValueError):
        pooled_relation(history(20), 26)
    assert rolling_symmetry(history(20)) == []
