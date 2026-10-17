"""Causal tensor anchors, fixed IID scaling, and research-only validation."""
import importlib.util
import json

import numpy as np
import pytest


def history(length=100, seed=17):
    rng = np.random.default_rng(seed)
    x = np.zeros((length, 45), dtype=int)
    for row in x:
        row[rng.choice(45, size=6, replace=False)] = 1
    return x


def test_representation_module_exists():
    assert importlib.util.find_spec('src.analysis.tensor_representation') is not None


def test_tensor_shapes_one_based_anchors_and_feature_names():
    from src.analysis.tensor_representation import build_tensors
    tensors = build_tensors(history(), normalize=False)
    expected = {
        'A': (27, ['lag_0', 'lag_1', 'lag_2', 'lag_4', 'lag_8', 'lag_13', 'lag_26']),
        'B': (52, ['rate_10', 'rate_26', 'rate_52']),
        'C': (52, ['appearance', 'gap_52', 'rate_26', 'rate_52']),
    }
    assert set(tensors) == set(expected)
    for name, (start, features) in expected.items():
        tensor = tensors[name]
        assert tensor['values'].shape == (101 - start, 45, len(features))
        np.testing.assert_array_equal(tensor['draws'], np.arange(start, 101))
        assert tensor['features'] == features
        assert np.isfinite(tensor['values']).all()


def test_lag_features_use_completed_anchor_and_exact_past_rows():
    from src.analysis.tensor_representation import build_tensors
    x = history()
    tensor = build_tensors(x, normalize=False)['A']
    for index, anchor in [(0, 27), (43, 70), (-1, 100)]:
        for feature, lag in enumerate([0, 1, 2, 4, 8, 13, 26]):
            np.testing.assert_array_equal(tensor['values'][index, :, feature], x[anchor - 1 - lag])


@pytest.mark.parametrize('window,feature', [(10, 0), (26, 1), (52, 2)])
def test_rolling_rates_include_anchor_without_future(window, feature):
    from src.analysis.tensor_representation import build_tensors
    x = history()
    tensors = build_tensors(x, normalize=False)
    for index, anchor in [(0, 52), (18, 70), (-1, 100)]:
        expected = x[anchor - window:anchor].mean(axis=0)
        np.testing.assert_allclose(tensors['B']['values'][index, :, feature], expected)
        if window != 10:
            np.testing.assert_allclose(tensors['C']['values'][index, :, feature + 1], expected)


def test_gap_current_appearance_zero_previous_appearance_and_never_seen():
    from src.analysis.tensor_representation import build_tensors
    x = np.zeros((60, 45), dtype=int)
    x[:, :6] = 1
    x[0, 5] = 0
    x[0, 6] = 1
    x[50, 5] = 0
    x[50, 7] = 1
    x[51, 5] = 0
    x[51, 8] = 1
    c = build_tensors(x, normalize=False)['C']['values']
    np.testing.assert_array_equal(c[0, :, 0], x[51])
    np.testing.assert_allclose(c[0, [5, 6, 7, 8, 9], 1], [2/52, 51/52, 1/52, 0, 1])
    assert c[1, 5, 1] == 0
    assert c[1, 6, 1] == 1
    assert c[-1, 9, 1] == 1
    np.testing.assert_array_equal(c, build_tensors(x.copy(), normalize=False)['C']['values'])


@pytest.mark.parametrize('normalize', [False, True])
def test_prefix_values_do_not_depend_on_future_rows_or_fitted_scaling(normalize):
    from src.analysis.tensor_representation import build_tensors
    x = history(140)
    prefix = build_tensors(x[:80], cutoff=80, normalize=normalize)
    complete = build_tensors(x, cutoff=140, normalize=normalize)
    for name in prefix:
        count = len(prefix[name]['draws'])
        np.testing.assert_array_equal(prefix[name]['values'], complete[name]['values'][:count])
        np.testing.assert_array_equal(prefix[name]['draws'], complete[name]['draws'][:count])


def test_normalization_uses_fixed_iid_moments_including_clipped_gap():
    from src.analysis.tensor_representation import build_tensors
    x = history()
    raw, scaled = build_tensors(x, normalize=False), build_tensors(x)
    p = 6 / 45
    # Independent distribution calculation: G=0..51, with tail mass at 52.
    support = np.arange(53, dtype=float) / 52
    probability = np.r_[p * (1-p) ** np.arange(52), (1-p) ** 52]
    gap_mean = float(probability @ support)
    gap_sd = float(np.sqrt(probability @ (support - gap_mean)**2))
    moments = {
        'A': ([p] * 7, [np.sqrt(p*(1-p))] * 7),
        'B': ([p] * 3, np.sqrt(p*(1-p) / np.array([10, 26, 52]))),
        'C': ([p, gap_mean, p, p], [np.sqrt(p*(1-p)), gap_sd,
                                     np.sqrt(p*(1-p)/26), np.sqrt(p*(1-p)/52)]),
    }
    for name, (mean, sd) in moments.items():
        np.testing.assert_allclose(scaled[name]['values'], (raw[name]['values'] - mean) / sd,
                                   rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(scaled[name]['metadata']['iid_mean'], mean)
        np.testing.assert_allclose(scaled[name]['metadata']['iid_std'], sd)


def test_metadata_serializes_without_nan_and_records_reproducible_scaling():
    from src.analysis.tensor_representation import build_tensors
    for normalize in [False, True]:
        tensors = build_tensors(history(52), cutoff=52, normalize=normalize)
        for name, tensor in tensors.items():
            metadata = json.loads(json.dumps(tensor['metadata'], allow_nan=False))
            assert metadata['cutoff'] == 52
            assert metadata['first_draw'] == (27 if name == 'A' else 52)
            assert metadata['last_draw'] == 52
            assert metadata['normalized'] is normalize
            assert metadata['normalization'] == ('fixed_iid' if normalize else 'none')


@pytest.mark.parametrize('cutoff', [0, 51, 79, 81, 1246, 80.0, True, '80'])
def test_cutoff_requires_exact_integer_prefix_length(cutoff):
    from src.analysis.tensor_representation import build_tensors
    with pytest.raises(ValueError, match='cutoff'):
        build_tensors(history(80), cutoff=cutoff)


def test_cutoff_accepts_numpy_integer_and_does_not_mutate_input():
    from src.analysis.tensor_representation import build_tensors
    x = history(52)
    original = x.copy()
    tensors = build_tensors(x, cutoff=np.int64(52))
    assert tensors['B']['values'].shape == (1, 45, 3)
    np.testing.assert_array_equal(x, original)


@pytest.mark.parametrize('length', [2, 26, 51])
def test_minimum_complete_history_is_52(length):
    from src.analysis.tensor_representation import build_tensors
    with pytest.raises(ValueError, match='52'):
        build_tensors(history(length))


def test_synthetic_row_1246_is_rejected_even_with_earlier_cutoff():
    from src.analysis.tensor_representation import build_tensors
    for cutoff in [None, 1245, 1246]:
        with pytest.raises(ValueError, match='1245'):
            build_tensors(history(1246), cutoff=cutoff)


@pytest.mark.parametrize('bad', ['width', 'nonbinary', 'five', 'nan'])
def test_research_matrix_contract_is_preserved(bad):
    from src.analysis.tensor_representation import build_tensors
    x = history(60).astype(float)
    if bad == 'width':
        x = x[:, :-1]
    elif bad == 'nonbinary':
        x[0, np.flatnonzero(x[0])[0]] = 2
    elif bad == 'five':
        x[0, np.flatnonzero(x[0])[0]] = 0
    else:
        x[0, 0] = np.nan
    with pytest.raises(ValueError):
        build_tensors(x)
