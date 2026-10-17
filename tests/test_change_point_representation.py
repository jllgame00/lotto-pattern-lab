"""Synthetic checks for the frozen, causal H18 representations."""
import importlib.util
import json

import numpy as np
import pytest


def draws(n=120, seed=19):
    rng = np.random.default_rng(seed)
    x = np.zeros((n, 45), dtype=bool)
    for row in x:
        row[rng.choice(45, 6, replace=False)] = True
    return x


def test_representation_module_exists():
    assert importlib.util.find_spec('src.analysis.change_point_representation') is not None


def test_shape_vector_has_exact_frozen_seven_features():
    from src.analysis.change_point_representation import SHAPE_FEATURES, shape_vector
    from src.analysis.recurrence import EmbeddingConfig, observations

    x = draws(12)
    x[0] = False
    x[0, [0, 1, 5, 9, 19, 44]] = True
    shape = shape_vector(x)
    assert SHAPE_FEATURES == ('sum', 'range', 'std', 'spacing_mean',
                              'spacing_std', 'consecutive_pairs', 'odd_count')
    expected = observations(x, EmbeddingConfig('B', metric='euclidean'))[:, [0, 5, 2, 6, 7, 10, 11]]
    np.testing.assert_allclose(shape, expected, rtol=0, atol=0)
    np.testing.assert_allclose(shape[0], [84, 44, np.std([1, 2, 6, 10, 20, 45]),
                                         8.8, np.std([1, 4, 4, 10, 25]), 1, 2])


@pytest.mark.parametrize('block,complete,tail', [(13, 117, 3), (26, 104, 16), (52, 104, 16)])
def test_blocks_start_at_draw_one_and_discard_incomplete_tail(block, complete, tail):
    from src.analysis.change_point_representation import block_frequency

    x = draws()
    result = block_frequency(x, block)
    assert result['block_size'] == block
    assert result['used_draws'] == complete
    assert result['discarded_tail'] == tail
    assert result['counts'].shape == (complete // block, 45)
    np.testing.assert_array_equal(result['ends'], np.arange(block, complete + 1, block))
    np.testing.assert_array_equal(result['counts'][0], x[:block].sum(axis=0))
    np.testing.assert_array_equal(result['counts'][-1], x[complete-block:complete].sum(axis=0))
    np.testing.assert_allclose(result['rates'], result['counts'] / block)
    np.testing.assert_array_equal(result['counts'].sum(axis=1), 6 * block)
    changed = x.copy()
    changed[complete:] = np.roll(changed[complete:], 1, axis=1)
    np.testing.assert_array_equal(block_frequency(changed, block)['counts'], result['counts'])


@pytest.mark.parametrize('n,step,want', [
    (0, 13, [0]), (13, 13, [0, 13]), (27, 13, [0, 13, 26, 27]),
    (26, 13, [0, 13, 26]), (9, 4, [0, 4, 8, 9]),
])
def test_grid_endpoints_include_final_draw_once(n, step, want):
    from src.analysis.change_point_representation import grid_endpoints
    actual = grid_endpoints(n, step)
    assert np.issubdtype(actual.dtype, np.integer)
    np.testing.assert_array_equal(actual, want)


@pytest.mark.parametrize('n,step', [(-1, 13), (1.0, 13), (True, 13), (10, 0), (10, -1), (10, 2.5), (10, True)])
def test_grid_rejects_invalid_lengths_and_steps(n, step):
    from src.analysis.change_point_representation import grid_endpoints
    with pytest.raises(ValueError):
        grid_endpoints(n, step)


def test_context_dimensions_endpoints_and_parameter_counts():
    from src.analysis.change_point_representation import build_contexts
    contexts = build_contexts(draws(), cutoff=120)
    assert set(contexts) == {'number', 'A', 'B13', 'B26', 'B52', 'C'}
    for name, dimension in [('number', 1), ('A', 45), ('C', 7)]:
        ctx = contexts[name]
        assert ctx['dimension'] == dimension
        assert ctx['observations'] == ctx['used_draws'] == 120
        assert ctx['discarded_tail'] == 0
        np.testing.assert_array_equal(ctx['endpoints'], [0, 13, 26, 39, 52, 65, 78, 91, 104, 117, 120])
        shape = (11, 11, 45) if name == 'number' else (11, 11)
        assert ctx['costs'].shape == shape
    np.testing.assert_allclose(contexts['A']['costs'], contexts['number']['costs'].sum(axis=2))
    for block in (13, 26, 52):
        ctx = contexts[f'B{block}']
        q = 120 // block
        assert ctx['dimension'] == 45
        assert ctx['observations'] == q
        assert ctx['used_draws'] == block * q
        assert ctx['discarded_tail'] == 120 % block
        assert ctx['costs'].shape == (q + 1, q + 1)
        np.testing.assert_array_equal(ctx['endpoints'], np.arange(q + 1) * block)
        assert 'tail' in json.dumps(ctx['metadata']).lower()
    for ctx in contexts.values():
        assert ctx['kind']
        json.dumps(ctx['metadata'], allow_nan=False)


def test_block_gaussian_costs_use_fixed_iid_scale_and_unit_block_indices():
    from src.analysis.change_point_representation import build_contexts
    x = draws()
    for block in (13, 26, 52):
        ctx = build_contexts(x)[f'B{block}']
        q = len(x) // block
        rates = np.array([x[i*block:(i+1)*block].mean(axis=0) for i in range(q)])
        p = 6 / 45
        z = (rates - p) / np.sqrt(p * (1-p) / block)
        expected = ((z - z.mean(axis=0)) ** 2).sum()
        assert ctx['costs'][0, -1] == pytest.approx(expected)
        np.testing.assert_allclose(ctx['rates'], rates)
        np.testing.assert_allclose(ctx['standardized'], z)


def test_shape_scaler_is_fit_only_on_exact_supplied_prefix():
    from src.analysis.change_point_representation import build_contexts, shape_vector
    x = draws(140)
    prefix = x[:120]
    c = build_contexts(prefix, cutoff=120)['C']
    shape = shape_vector(prefix)
    np.testing.assert_allclose(c['metadata']['mean'], shape.mean(axis=0))
    np.testing.assert_allclose(c['metadata']['std'], shape.std(axis=0, ddof=0))
    z = (shape - shape.mean(axis=0)) / shape.std(axis=0)
    np.testing.assert_allclose(c['standardized'], z)
    assert c['costs'][0, -1] == pytest.approx(((z-z.mean(axis=0))**2).sum())
    with pytest.raises(ValueError, match='prefix|cutoff'):
        build_contexts(x, cutoff=120)
    np.testing.assert_array_equal(c['standardized'], build_contexts(prefix.copy())['C']['standardized'])


def test_constant_shape_scales_are_one_and_costs_are_zero():
    from src.analysis.change_point_representation import build_contexts
    x = np.zeros((104, 45), dtype=bool)
    x[:, :6] = True
    c = build_contexts(x)['C']
    np.testing.assert_array_equal(c['metadata']['std'], np.ones(7))
    np.testing.assert_array_equal(c['standardized'], np.zeros((104, 7)))
    assert c['costs'][0, -1] == 0


@pytest.mark.parametrize('cutoff', [119, 121, 120.0, True])
def test_context_rejects_nonexact_cutoffs(cutoff):
    from src.analysis.change_point_representation import build_contexts
    with pytest.raises(ValueError, match='prefix|cutoff'):
        build_contexts(draws(), cutoff=cutoff)


@pytest.mark.parametrize('bad', [np.zeros((120, 45)), np.ones((120, 44)), np.ones((1246, 45)), np.ones(45)])
def test_all_representations_reject_invalid_research_input(bad):
    from src.analysis.change_point_representation import block_frequency, build_contexts, shape_vector
    for function in (shape_vector, build_contexts, lambda x: block_frequency(x, 13)):
        with pytest.raises(ValueError):
            function(bad)


def test_draw_ceiling_and_minimum_complete_blocks():
    from src.analysis.change_point_representation import build_contexts, shape_vector
    with pytest.raises(ValueError):
        shape_vector(draws(1246))
    with pytest.raises(ValueError, match='104|history|block'):
        build_contexts(draws(103))
    assert build_contexts(draws(104))['B52']['observations'] == 2


@pytest.mark.parametrize('block', [0, -13, 13.0, True, 10])
def test_block_frequency_rejects_unregistered_blocks(block):
    from src.analysis.change_point_representation import block_frequency
    with pytest.raises(ValueError):
        block_frequency(draws(), block)
