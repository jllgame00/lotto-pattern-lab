"""Causal historical scoring and independently counted information contexts."""
import importlib

import numpy as np
import pytest


def models():
    return importlib.import_module('src.models.information_flow')


def draws(n=700, seed=7, planted=False, lag=1):
    rng = np.random.default_rng(seed)
    x = np.zeros((n, 45), dtype=bool)
    if not planted:
        for row in x:
            row[rng.choice(45, 6, replace=False)] = True
        return x
    source = rng.random(n) < .5
    target = np.r_[np.zeros(lag, bool), source[:-lag]] ^ (rng.random(n) < .1)
    x[:, 0] = x[:, 2] = source
    x[:, 1] = target
    for row in x:
        row[rng.choice(np.arange(3, 45), 6 - int(row.sum()), replace=False)] = True
    return x


@pytest.mark.parametrize('name,kwargs', [
    ('MutualInformationModel', {}),
    ('TransferEntropyModel', {'k': 2, 'l': 2}),
    ('TargetHistoryBaseline', {'k': 2, 'l': 2}),
])
def test_models_require_exact_unchanged_historical_prefix(name, kwargs):
    cls = getattr(models(), name)
    x = draws()
    with pytest.raises(ValueError):
        cls(**kwargs).fit(x[:299], cutoff=299)
    with pytest.raises(ValueError):
        cls(**kwargs).fit(x[:400], cutoff=399)
    model = cls(**kwargs).fit(x[:400], cutoff=400)
    score = model.score_matrix(x[:650], target=651)
    assert list(score) == list(range(1, 46))
    assert all(np.isfinite(v) and 1e-6 <= v <= 1 - 1e-6 for v in score.values())
    assert score == model.score_matrix(x[:650], target=651)
    mutated = x[:650].copy()
    mutated[10] = np.roll(mutated[10], 1)
    with pytest.raises(ValueError):
        model.score_matrix(mutated, target=651)
    for past, target in [(x[:650], 650), (x[:399], 400), (draws(1245), 1246)]:
        with pytest.raises(ValueError):
            model.score_matrix(past, target=target)
    invalid = x[:650].copy()
    invalid[0, 0] = not invalid[0, 0]
    with pytest.raises(ValueError):
        model.score_matrix(invalid, target=651)


def test_declared_grid_rejects_unsupported_information_models():
    m = models()
    for cls, kwargs in [
        (m.MutualInformationModel, {'lag': 5}),
        (m.MutualInformationModel, {'incoming': 4}),
        (m.TransferEntropyModel, {'lag': 0}),
        (m.TransferEntropyModel, {'k': 3}),
        (m.TransferEntropyModel, {'l': 0}),
        (m.TargetHistoryBaseline, {'k': 0}),
    ]:
        with pytest.raises(ValueError):
            cls(**kwargs)


def test_mi_planted_source_ties_and_conditional_shrinkage():
    x = draws(planted=True)
    model = models().MutualInformationModel(incoming=3).fit(x[:400], cutoff=400)
    scores = model.score_matrix(x, target=701)
    diagnostic = model.last_diagnostic[1]
    selected = diagnostic['selected']
    assert [edge['source'] for edge in selected[:2]] == [1, 3]
    assert all(edge['source'] != 2 for edge in selected)
    window = x[-624:]
    base = float(window[1:, 1].mean())
    assert diagnostic['baseline'] == pytest.approx(base)
    expected = 0.
    for edge in selected:
        i = edge['source'] - 1
        mask = window[:-1, i] == window[-1, i]
        support = int(mask.sum())
        conditional = (window[1:, 1][mask].sum() + 20 * base) / (support + 20)
        assert edge['context_support'] == support >= 20
        assert edge['conditional'] == pytest.approx(conditional)
        expected += edge['weight'] * conditional
    assert sum(edge['weight'] for edge in selected) == pytest.approx(1.)
    assert scores[2] == pytest.approx(expected)
    assert (scores[2] > base) == bool(x[-1, 0])


@pytest.mark.parametrize('lag,k,l', [(1, 1, 1), (4, 2, 2), (26, 1, 2)])
def test_te_target_history_baseline_uses_identical_aligned_context(lag, k, l):
    x = draws(seed=21)
    module = models()
    baseline = module.TargetHistoryBaseline(lag=lag, k=k, l=l).fit(x[:400], cutoff=400)
    te = module.TransferEntropyModel(lag=lag, k=k, l=l).fit(x[:400], cutoff=400)
    base_scores = baseline.score_matrix(x, target=701)
    te.score_matrix(x, target=701)
    window = x[-624:]
    start = max(lag + l - 1, k)
    for j in range(45):
        states = sum((1 << r) * window[start - 1 - r:len(window) - 1 - r, j].astype(int)
                     for r in range(k))
        current = sum((1 << r) * int(window[-1 - r, j]) for r in range(k))
        mask = states == current
        overall = window[start:, j].mean()
        expected = (window[start:, j][mask].sum() + 20 * overall) / (mask.sum() + 20)
        assert base_scores[j + 1] == pytest.approx(np.clip(expected, 1e-6, 1 - 1e-6))
        assert te.last_diagnostic[j]['baseline'] == pytest.approx(expected)


def test_sparse_te_falls_back_to_target_history_and_never_selects_self():
    x = np.zeros((700, 45), bool)
    x[:, :6] = True
    module = models()
    te = module.TransferEntropyModel(k=2, l=2).fit(x[:400], cutoff=400)
    baseline = module.TargetHistoryBaseline(k=2, l=2).fit(x[:400], cutoff=400)
    assert te.score_matrix(x, target=701) == baseline.score_matrix(x, target=701)
    assert all(not diagnostic['selected'] for diagnostic in te.last_diagnostic)


def test_te_planted_lagged_source_uses_matching_joint_history_context():
    x = draws(planted=True, lag=4, seed=1)
    model = models().TransferEntropyModel(lag=4, k=2, l=2).fit(x[:400], cutoff=400)
    scores = model.score_matrix(x, target=701)
    diagnostic = model.last_diagnostic[1]
    selected = diagnostic['selected']
    assert [edge['source'] for edge in selected[:2]] == [1, 3]
    assert all(edge['source'] != 2 for edge in selected)
    window = x[-624:]
    # Lag4, source depth2, and target depth2 require the first t at index5.
    own_states = window[4:-1, 1].astype(int) + 2 * window[3:-2, 1]
    own_current = int(window[-1, 1]) + 2 * int(window[-2, 1])
    own_mask = own_states == own_current
    own_base = (window[5:, 1][own_mask].sum() + 20 * window[5:, 1].mean()) / (own_mask.sum() + 20)
    expected = own_base
    for edge in selected:
        i = edge['source'] - 1
        states = window[1:-4, i].astype(int) + 2 * window[:-5, i]
        current = int(window[-4, i]) + 2 * int(window[-5, i])
        mask = (states == current) & own_mask
        conditional = (window[5:, 1][mask].sum() + 20 * own_base) / (mask.sum() + 20)
        assert edge['context_support'] == mask.sum() >= 20
        assert edge['conditional'] == pytest.approx(conditional)
        expected += edge['weight'] * (conditional - own_base)
    assert scores[2] == pytest.approx(expected)


def test_strong_te_edge_is_excluded_when_current_joint_context_has_under20_samples():
    # This seed ends in a rare contrary context, seen only8 times in training.
    x = draws(planted=True, lag=4, seed=7)
    model = models().TransferEntropyModel(lag=4, k=2, l=2).fit(x[:400], cutoff=400)
    model.score_matrix(x, target=701)
    assert not {1, 3}.intersection(edge['source'] for edge in model.last_diagnostic[1]['selected'])


def test_historical_upper_boundary_scores_without_mutating_fit_input():
    x = draws(1244)
    train = x[:400].copy()
    model = models().TransferEntropyModel().fit(train, cutoff=400)
    train[:] = np.roll(train, 1, axis=1)
    scores = model.score_matrix(x, target=1245)
    assert len(scores) == 45 and all(np.isfinite(list(scores.values())))


def test_window_recomputation_uses_only_current_prefix_and_shares_incoming_cache():
    module = models()
    x = draws(1000, seed=89)
    for cls, cache in [(module.MutualInformationModel, module._mi_matrix_cache),
                       (module.TransferEntropyModel, module._te_matrix_cache)]:
        cache.cache_clear()
        first = cls(incoming=3).fit(x[:300], cutoff=300)
        five = cls(incoming=5).fit(x[:300], cutoff=300)
        score = first.score_matrix(x[:800], target=801)
        after_first = cache.cache_info()
        five.score_matrix(x[:800], target=801)
        assert cache.cache_info().hits > after_first.hits
        assert cache.cache_info().misses == after_first.misses
        changed = x.copy()
        changed[810:] = np.roll(changed[810:], 1, axis=1)
        assert first.score_matrix(changed[:800], target=801) == score
        # Rows outside the trailing624 window cannot alter a later decomposition.
        changed = x.copy()
        changed[310:350] = np.roll(changed[310:350], 1, axis=1)
        independent = cls().fit(changed[:300], cutoff=300)
        assert first.score_matrix(x, target=1001) == independent.score_matrix(changed, target=1001)
