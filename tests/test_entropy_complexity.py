"""Hand-counted and synthetic checks for finite entropy proxies."""
import importlib.util
import math

import numpy as np
import pytest


def test_entropy_complexity_module_exists():
    assert importlib.util.find_spec('src.analysis.entropy_complexity') is not None


def test_shannon_uses_theoretical_alphabet_and_retains_unoccupied_counts():
    from src.analysis.entropy_complexity import shannon
    fair = shannon([0, 1] * 20, alphabet=4)
    assert fair['entropy'] == pytest.approx(1)
    assert fair['normalized'] == pytest.approx(.5)
    assert fair['samples'] == 40
    assert fair['occupied'] == 2
    assert sorted(fair['counts']) == [0, 0, 20, 20]
    assert fair['eligible']
    constant = shannon(['a'] * 30)
    assert constant['entropy'] == 0
    assert constant['normalized'] == 0
    assert constant['occupied'] == 1


def test_shannon_support_screen_keeps_full_sample_sum_alphabet_eligible():
    from src.analysis.entropy_complexity import shannon
    assert not shannon([0] * 9, alphabet=2)['eligible']
    assert shannon([0] * 10, alphabet=2)['eligible']
    assert not shannon(np.arange(234), alphabet=235)['eligible']
    result = shannon(np.arange(235), alphabet=235)
    assert result['eligible']
    assert result['normalized'] == pytest.approx(1)


def test_block_entropy_uses_overlapping_chronological_binary_words():
    from src.analysis.entropy_complexity import binary_block_entropy
    result = binary_block_entropy([0, 0, 1, 1, 0], L=2)
    np.testing.assert_array_equal(result['counts'], [1, 1, 1, 1])
    assert result['entropy'] == pytest.approx(2)
    assert result['per_symbol'] == pytest.approx(1)
    assert result['normalized'] == pytest.approx(1)
    assert result['samples'] == 4
    assert result['occupied'] == 4
    assert not result['eligible']
    assert binary_block_entropy([0, 1] * 30, L=2)['eligible']


def test_conditional_entropy_aligns_future_on_common_history_suffix():
    from src.analysis.entropy_complexity import conditional_entropy
    result = conditional_entropy([0, 0, 1, 1, 0], history=2)
    np.testing.assert_array_equal(result['counts'], [[0, 1], [0, 1], [0, 0], [1, 0]])
    np.testing.assert_array_equal(result['context_counts'], [1, 1, 0, 1])
    assert result['samples'] == 3
    assert result['entropy_future'] == pytest.approx(.9182958340544896)
    assert result['conditional'] == 0
    assert result['reduction'] == pytest.approx(.9182958340544896)
    assert not result['eligible']


def test_conditional_entropy_requires_all_contexts_and_both_future_symbols():
    from src.analysis.entropy_complexity import conditional_entropy
    alternating = conditional_entropy([0, 1] * 30, history=1)
    assert alternating['eligible']
    assert alternating['conditional'] == 0
    assert alternating['reduction'] > .99
    assert not conditional_entropy([0, 1] * 30, history=2)['eligible']
    constant = conditional_entropy([0] * 60, history=1)
    assert constant['entropy_future'] == 0
    assert constant['reduction'] == 0
    assert not constant['eligible']


def test_permutation_entropy_normalizes_full_pattern_alphabet_and_reports_ties():
    from src.analysis.entropy_complexity import permutation_entropy
    result = permutation_entropy([1, 1, 0, 2], m=3, tau=1)
    # Stable ordering gives (2,0,1), then (1,0,2): two distinct patterns.
    assert result['entropy'] == pytest.approx(1)
    assert result['normalized'] == pytest.approx(1 / math.log2(6))
    assert result['samples'] == 2
    assert result['occupied'] == 2
    np.testing.assert_array_equal(result['counts'], [0, 0, 1, 0, 1, 0])
    assert result['tie_fraction'] == .5
    assert not result['eligible']
    constant = permutation_entropy(np.ones(40), m=3, tau=2)
    assert constant['entropy'] == 0
    assert constant['tie_fraction'] == 1
    assert constant['occupied'] == 1


def test_permutation_entropy_random_exceeds_periodic_with_delayed_sample_count():
    from src.analysis.entropy_complexity import permutation_entropy
    periodic = permutation_entropy(np.tile([0., 1., 2., 3.], 300), m=4, tau=1)
    random = permutation_entropy(np.random.default_rng(160).normal(size=1200), m=4, tau=1)
    assert random['normalized'] > .98
    assert random['normalized'] > periodic['normalized'] + .4
    assert random['eligible']
    delayed = permutation_entropy(np.arange(50), m=5, tau=8)
    assert delayed['samples'] == 18
    assert delayed['entropy'] == 0
    assert not delayed['eligible']


@pytest.mark.parametrize('values,m', [([0, 0, 0, 0, 1, 0, 0], 2),
                                    ([0, 0, 0, 0, 0, 1, 0, 0, 0], 3)])
def test_sample_entropy_counts_common_templates_and_excludes_self_matches(values, m):
    from src.analysis.entropy_complexity import sample_entropy
    result = sample_entropy(values, m=m, r=.2)
    assert result['samples'] == len(values) - m
    assert result['B'] == 3
    assert result['A'] == 1
    assert result['entropy'] == pytest.approx(math.log(3))
    expected_std = math.sqrt(6) / 7 if m == 2 else math.sqrt(8) / 9
    assert result['std'] == pytest.approx(expected_std)
    assert result['radius'] == pytest.approx(.2 * expected_std)
    assert not result['eligible']


def test_sample_entropy_sparse_and_degenerate_results_never_return_infinity():
    from src.analysis.entropy_complexity import sample_entropy
    no_extension = sample_entropy([0, 0, 0, 1, 0, 0], m=2, r=.2)
    assert no_extension['B'] == 1
    assert no_extension['A'] == 0
    assert no_extension['entropy'] is None
    assert not no_extension['eligible']
    no_match = sample_entropy(np.arange(10), m=2, r=.15)
    assert no_match['B'] == 0
    assert no_match['entropy'] is None
    constant = sample_entropy(np.ones(10), m=2, r=.2)
    assert constant['samples'] == 8
    assert constant['A'] == constant['B'] == 28
    assert constant['std'] == constant['radius'] == 0
    assert constant['entropy'] == 0
    assert not constant['eligible']


def test_sample_entropy_independent_scalar_series_exceeds_periodic():
    from src.analysis.entropy_complexity import sample_entropy
    periodic = sample_entropy(np.tile([0., 1., 2., 3.], 150), m=2, r=.2)
    random = sample_entropy(np.random.default_rng(161).normal(size=1200), m=2, r=.2)
    assert periodic['entropy'] == 0
    assert periodic['eligible']
    assert random['entropy'] > 1.5
    assert random['eligible']


@pytest.mark.parametrize('values', [[], [[0, 1]], [0, np.nan], [0, np.inf]])
def test_estimators_reject_empty_nonfinite_and_nonvector_inputs(values):
    from src.analysis.entropy_complexity import (
        binary_block_entropy, conditional_entropy, permutation_entropy, sample_entropy, shannon,
    )
    for estimator in (shannon, binary_block_entropy, conditional_entropy, permutation_entropy, sample_entropy):
        with pytest.raises(ValueError):
            estimator(values)


def test_estimators_validate_binary_symbols_parameters_and_template_lengths():
    from src.analysis.entropy_complexity import (
        binary_block_entropy, conditional_entropy, permutation_entropy, sample_entropy, shannon,
    )
    calls = [
        lambda: shannon([0, 1], alphabet=1),
        lambda: shannon([0, 1], alphabet=True),
        lambda: binary_block_entropy([0, 2, 1]),
        lambda: binary_block_entropy([0, 1], L=0),
        lambda: binary_block_entropy([0, 1], L=3),
        lambda: conditional_entropy([0, 2, 1]),
        lambda: conditional_entropy([0, 1], history=2),
        lambda: conditional_entropy([0, 1, 0], history=3),
        lambda: permutation_entropy([0, 1], m=3),
        lambda: permutation_entropy(np.arange(20), m=True),
        lambda: permutation_entropy(np.arange(20), tau=0),
        lambda: sample_entropy([0, 1], m=2),
        lambda: sample_entropy(np.arange(20), r=0),
        lambda: sample_entropy(np.arange(20), r=np.inf),
    ]
    for call in calls:
        with pytest.raises(ValueError):
            call()
