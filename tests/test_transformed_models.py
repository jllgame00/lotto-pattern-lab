"""Causal transformed-space model behavior on synthetic six-of-45 histories."""
import numpy as np
import pytest

from src.analysis.spatiotemporal import iid_surrogate
from src.models.transformed_space import (
    ModularResidueModel, DifferenceRelationModel, GapShapeModel,
    ModularDifferenceConsensus,
)


def rows(numbers, count):
    x = np.zeros((count, 45), dtype=bool)
    x[:, np.array(numbers) - 1] = True
    return x


@pytest.mark.parametrize('cls', [ModularResidueModel, DifferenceRelationModel, GapShapeModel])
def test_exact_prefix_guards_and_training_copy(cls):
    x = iid_surrogate(1245, seed=150043)
    model = cls().fit(x[:104], cutoff=104)
    before = model.score_matrix(x[:104], target=105)
    assert set(before) == set(range(1, 46))
    assert np.isfinite(list(before.values())).all()
    for bad_cutoff in (103, 105, True):
        with pytest.raises(ValueError):
            cls().fit(x[:104], cutoff=bad_cutoff)
    with pytest.raises(ValueError):
        cls().fit(x[:103], cutoff=103)
    with pytest.raises(ValueError):
        cls().fit(iid_surrogate(1246, seed=8), cutoff=1246)
    with pytest.raises(ValueError):
        cls().score_matrix(x[:104], target=105)
    for target in (104, 106, True, 1246):
        with pytest.raises(ValueError):
            model.score_matrix(x[:104], target=target)
    changed = x[:104].copy()
    changed[0] = x[104]
    with pytest.raises(ValueError):
        model.score_matrix(changed, target=105)
    original = x[:104].copy()
    model.fit(original, cutoff=104)
    original[0] = x[104]
    assert model.score_matrix(x[:104], target=105) == before


def test_modular_conditional_shrinkage_and_unequal_class_populations():
    x = rows([1, 3, 5, 7, 9, 11], 120)
    x[1::2] = rows([2, 4, 6, 8, 10, 12], 60)
    model = ModularResidueModel(modulus=2).fit(x, cutoff=120)
    score = model.score_matrix(x, target=121)
    # 119 future draws: 59 all-odd and 60 all-even. Last source is all-even.
    base_even, base_odd = 360 / 119, 354 / 119
    want_even = (50 * base_even) / (59 + 50) / 22
    want_odd = (354 + 50 * base_odd) / (59 + 50) / 23
    assert score[2] == pytest.approx(want_even)
    assert score[1] == pytest.approx(want_odd)
    assert score[44] == score[2] and score[45] == score[1]
    even = model.last_diagnostic[1]
    assert even['source_draw'] == 120 and even['state'] == 6
    assert even['support'] == 59 and even['baseline'] == pytest.approx(base_even)
    assert even['conditional'] / 22 == pytest.approx(score[2])


def test_modular_unsupported_current_state_uses_baseline_and_lag_source():
    x = rows([1, 3, 5, 7, 9, 11], 120)
    x[-2] = rows([2, 4, 6, 8, 10, 12], 1)[0]
    model = ModularResidueModel(modulus=2, lag=2).fit(x, cutoff=120)
    score = model.score_matrix(x, target=121)
    d = model.last_diagnostic[1]
    assert d['source_draw'] == 119 and d['state'] == 6 and d['support'] == 0
    assert score[2] == pytest.approx((6 / 118) / 22)
    assert d['conditional'] == d['baseline']


def test_difference_weights_exclude_self_and_remove_boundary_opportunity():
    x = rows([1, 2, 3, 4, 5, 6], 120)
    model = DifferenceRelationModel().fit(x, cutoff=120)
    score = model.score_matrix(x, target=121)
    p = 6 / 45
    # d=1..5 each appears 2*(6-d) times; opportunities=(12-d) per row.
    weights = [((2 * (6-d) * 119 + 100*p) / ((12-d)*119 + 100)) / p - 1
               for d in range(1, 6)]
    assert score[1] == pytest.approx(sum(weights) * (1/6 - 1/45))
    assert score[45] == pytest.approx(-sum(weights) / 45)
    d = model.last_diagnostic[0]
    assert d['source_draw'] == 120 and d['source_numbers'] == [1, 2, 3, 4, 5, 6]
    assert d['distances'] == [0, 1, 2, 3, 4, 5]
    assert d['weights'][0] == 0
    assert d['boundary_term'] == pytest.approx(sum(weights) / 45)
    assert d['score'] == pytest.approx(score[1])


def test_difference_support_threshold_is_observed_count_and_source_is_lagged():
    x = rows([1, 2, 3, 4, 5, 6], 104)
    x[-2] = rows([40, 41, 42, 43, 44, 45], 1)[0]
    model = DifferenceRelationModel(lag=2, support=40).fit(x, cutoff=104)
    model.score_matrix(x, target=105)
    assert model.last_diagnostic[0]['source_draw'] == 103
    assert model.last_diagnostic[0]['source_numbers'] == [40, 41, 42, 43, 44, 45]
    # d=44 occurs only twice: it is unsupported despite abundant opportunities.
    assert model.last_diagnostic[0]['weights'][-1] == 0


def test_gap_shape_stable_neighbors_use_actual_successors_and_bounded_kernels():
    x = rows([1, 2, 3, 4, 5, 6], 140)
    x[1:11] = rows([20, 21, 22, 23, 24, 25], 10)
    x[-1] = rows([40, 41, 42, 43, 44, 45], 1)[0]
    model = GapShapeModel(K=10, sigma=1).fit(x, cutoff=140)
    score = model.score_matrix(x, target=141)
    number = np.arange(1, 46)
    kernels = np.exp(-.5 * (number[None, :] - np.arange(20, 26)[:, None])**2)
    expected = (kernels / kernels.sum(axis=1, keepdims=True)).mean(axis=0)
    np.testing.assert_allclose(list(score.values()), expected, atol=1e-15)
    diag = model.last_diagnostic
    assert diag[0]['neighbor_draws'] == list(range(1, 11))
    assert diag[0]['successor_draws'] == list(range(2, 12))
    assert max(diag[0]['neighbor_draws']) <= 140 - 26
    assert sum(score.values()) == pytest.approx(1)


@pytest.mark.parametrize('cls,kwargs', [
    (ModularResidueModel, {'modulus': 8}), (ModularResidueModel, {'lag': 5}),
    (ModularResidueModel, {'modulus': True}), (DifferenceRelationModel, {'support': 21}),
    (DifferenceRelationModel, {'lag': 0}), (GapShapeModel, {'K': 11}),
    (GapShapeModel, {'sigma': 3}), (GapShapeModel, {'K': True}),
])
def test_models_reject_outside_declared_development_grid(cls, kwargs):
    with pytest.raises(ValueError):
        cls(**kwargs)


def test_consensus_equal_inverse_ranks_and_configuration():
    x = iid_surrogate(110, seed=500)
    modular, difference = ModularResidueModel(), DifferenceRelationModel()
    model = ModularDifferenceConsensus(modular, difference).fit(x, cutoff=110)
    score = model.score_matrix(x, target=111)
    parents = [m.fit(x, cutoff=110).score_matrix(x, target=111) for m in (modular, difference)]
    ranks = [{n: i+1 for i, n in enumerate(sorted(s, key=lambda n: (-s[n], n)))} for s in parents]
    assert score == {n: -(ranks[0][n] + ranks[1][n]) / 2 for n in range(1, 46)}
    assert model.configuration()['modular'] == modular.configuration()
    assert model.configuration()['difference'] == difference.configuration()


@pytest.mark.parametrize('target', [901, 1245])
def test_actual_dependency_inputs_use_scoring_prefix(monkeypatch, target):
    import src.models.transformed_space as module
    x = iid_surrogate(1245, seed=94)
    seen = {'modular': [], 'difference': [], 'shape': []}
    for name, dependency in [('modular', 'transition'), ('difference', 'absolute_relation'),
                             ('shape', 'difference_representation')]:
        original = getattr(module, dependency)
        def traced(values, *args, _original=original, _name=name, **kwargs):
            seen[_name].append(values.copy())
            return _original(values, *args, **kwargs)
        monkeypatch.setattr(module, dependency, traced)
    module._modular_context.cache_clear()
    module._difference_context.cache_clear()
    module._shape_context.cache_clear()
    for cls in (ModularResidueModel, DifferenceRelationModel, GapShapeModel):
        model = cls().fit(x[:900], cutoff=900)
        model.score_matrix(x[:target-1], target=target)
        with pytest.raises(ValueError):
            model.score_matrix(x, target=target)
    for inputs in seen.values():
        assert len(inputs) == 1
        assert np.array_equal(inputs[0], x[:target-1])


def test_shape_nearest_recent_match_is_excluded_at_26_draw_boundary():
    x = rows([1, 2, 4, 8, 16, 32], 140)
    x[113] = rows([1, 2, 3, 4, 5, 6], 1)[0]  # query-26, eligible
    x[114] = rows([40, 41, 42, 43, 44, 45], 1)[0]  # query-25, ineligible
    x[-1] = rows([20, 21, 22, 23, 24, 25], 1)[0]
    model = GapShapeModel().fit(x, cutoff=140)
    score = model.score_matrix(x, target=141)
    assert model.last_diagnostic[0]['neighbor_draws'] == [114] + list(range(1, 10))
    centers = np.array([[40, 41, 42, 43, 44, 45]] + [[1, 2, 4, 8, 16, 32]] * 9)
    kernel = np.exp(-.5 * (np.arange(1, 46) - centers[..., None])**2)
    kernel /= kernel.sum(axis=-1, keepdims=True)
    np.testing.assert_allclose(list(score.values()), kernel.mean(axis=(0, 1)))
