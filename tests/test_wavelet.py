"""Synthetic wavelet checks; these tests never read draw history."""
import json

import numpy as np
import pytest

from src.analysis.wavelet import localized_regions, morlet_transform, summarize_wavelet


def test_transform_recovers_a_sinusoid_and_uses_time_by_series_orientation():
    t = np.arange(512)
    values = np.column_stack([np.sin(2 * np.pi * t / 20), np.cos(2 * np.pi * t / 39)])
    result = morlet_transform(values)
    assert result['coefficients'].shape == (2, 8, 512)
    np.testing.assert_allclose(result['power'], abs(result['coefficients']) ** 2)
    rows = summarize_wavelet(result, names=['twenty', 'thirty-nine'])
    assert [row['dominant_period'] for row in rows] == [20., 39.]
    assert [row['name'] for row in rows] == ['twenty', 'thirty-nine']
    assert np.mean(result['dominant_period_by_time'][0, 100:400] == 20) > .95
    assert all(0 < row['global_concentration'] <= 1 for row in rows)
    json.dumps(rows, allow_nan=False)


def test_variance_normalization_is_affine_invariant_and_constants_are_zero():
    t = np.arange(512)
    values = np.sin(2 * np.pi * t / 20)
    base = morlet_transform(values, periods=[8, 20, 52])
    changed = morlet_transform(17 + 3 * values, periods=[8, 20, 52])
    np.testing.assert_allclose(base['power'], changed['power'], atol=1e-12)
    assert base['normalization']['mean'][0] == pytest.approx(values.mean())
    assert base['normalization']['std'][0] == pytest.approx(values.std())
    constant = morlet_transform(np.ones(64), periods=[4, 8])
    assert np.count_nonzero(constant['coefficients']) == 0
    row = summarize_wavelet(constant)[0]
    assert row['max_localized_power'] == 0
    assert row['global_concentration'] == 0
    assert row['dominant_period'] is None
    assert localized_regions(constant) == []


def test_cone_masks_edges_and_unit_energy_kernel_gives_unit_impulse_energy():
    # Balanced, widely separated impulses avoid the step introduced when a
    # centered single impulse is zero padded at the record boundaries.
    impulse = np.zeros(2048)
    impulse[512], impulse[1536] = 1, -1
    result = morlet_transform(impulse, periods=[8, 20, 52])
    distance = np.minimum(np.arange(2048), np.arange(2048)[::-1])
    np.testing.assert_array_equal(result['valid'], distance[None, :] >= np.sqrt(2) * result['scale'][:, None])
    assert not result['valid'][:, 0].any()
    assert result['valid'][:, 256].all()
    # Two isolated impulses each contribute one unit of kernel energy.
    np.testing.assert_allclose(result['power'].sum(axis=2)[0] * impulse.std() ** 2, 2, atol=1e-6)


def test_burst_is_localized_and_short_or_cone_only_patches_are_excluded():
    t = np.arange(768)
    burst = np.zeros(768)
    burst[240:480] = np.sin(2 * np.pi * t[240:480] / 20)
    result = morlet_transform(burst, periods=[8, 13, 20, 26, 39, 52])
    regions = localized_regions(result, names=['burst'])
    assert regions
    strongest = max(regions, key=lambda row: row['score'])
    assert strongest['name'] == 'burst'
    assert strongest['period'] == 20
    assert 200 <= strongest['start'] <= 280
    assert 440 <= strongest['end'] <= 520
    assert strongest['duration'] >= 2 * strongest['period']
    assert 0 < strongest['scale_stability'] <= 1
    json.dumps(regions, allow_nan=False)
    # Hand-built powers isolate connectivity, cone exclusion and cycle guard.
    artificial = morlet_transform(np.zeros(128), periods=[8, 13])
    artificial['power'][:] = 0
    artificial['power'][0, 0, 40:48] = 10
    artificial['power'][0, :, :5] = 100
    assert localized_regions(artificial) == []


def test_region_score_and_one_based_bounds_use_only_connected_valid_cells():
    result = morlet_transform(np.zeros(128), periods=[8, 13])
    result['power'][0, 0, 30:50] = 6
    region = localized_regions(result, threshold=4)[0]
    assert region['start'] == 31 and region['end'] == 50
    assert region['duration'] == 20
    assert region['score'] == pytest.approx(40 / np.sqrt(20))
    assert region['scale_stability'] == 1
    assert region['max_power'] == 6


@pytest.mark.parametrize('values', [[], np.zeros((4, 0)), np.zeros((2, 2, 2)), [1, np.nan] * 16, [np.inf] * 32])
def test_invalid_values_are_rejected(values):
    with pytest.raises(ValueError):
        morlet_transform(values, periods=[4])


@pytest.mark.parametrize('periods', [[], [True], ['8'], [3], [0], [np.inf], [np.nan], [8, 8], [17], [[8]]])
def test_invalid_or_unsupported_periods_are_rejected(periods):
    with pytest.raises(ValueError):
        morlet_transform(np.zeros(64), periods=periods)


def test_summary_arguments_are_validated_and_transform_is_deterministic():
    values = np.random.default_rng(18).binomial(1, .13, size=(512, 2))
    first = morlet_transform(values)
    second = morlet_transform(values)
    np.testing.assert_array_equal(first['coefficients'], second['coefficients'])
    for function in (localized_regions, summarize_wavelet):
        for kwargs in ({'names': ['only-one']}, {'min_cycles': 1}, {'min_cycles': np.nan}, {'threshold': -1}, {'threshold': np.inf}):
            with pytest.raises(ValueError):
                function(first, **kwargs)
