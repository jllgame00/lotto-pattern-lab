"""Independent numerical contracts for the Phase 21 memory estimators."""
import numpy as np
import pytest

from src.analysis.long_memory import (
    SCALES, crossover, dfa, profile, rs_estimate, supported_scales,
)


def test_profile_demeans_each_column_and_preserves_input_dimension():
    x = np.array([[1., 10.], [3., 4.], [2., 7.]])
    np.testing.assert_allclose(profile(x), [[-1., 3.], [0., 0.], [0., 0.]])
    np.testing.assert_allclose(profile(x[:, 0]), [-1., 0., 0.])
    np.testing.assert_array_equal(profile(np.full(100, 10 / 3)), np.zeros(100))


def test_scale_support_counts_one_orientation_only():
    np.testing.assert_array_equal(supported_scales(1245), SCALES[:-1])
    np.testing.assert_array_equal(supported_scales(1248), SCALES)
    np.testing.assert_array_equal(supported_scales(31, (8, 13)), [])
    np.testing.assert_array_equal(supported_scales(32, (8, 13)), [8])


def test_dfa_matches_direct_forward_reverse_least_squares():
    x = np.random.default_rng(21).normal(size=(39, 2))
    result = dfa(x, scales=(8,))
    integrated = np.cumsum(x - x.mean(axis=0), axis=0)
    squares = []
    for start in [0, 8, 16, 24, 7, 15, 23, 31]:
        block = integrated[start:start + 8]
        fitted = np.column_stack([
            np.polyval(np.polyfit(np.arange(8), block[:, j], 1), np.arange(8))
            for j in range(2)
        ])
        squares.append((block - fitted) ** 2)
    expected = np.sqrt(np.mean(squares, axis=(0, 1)))
    np.testing.assert_allclose(result['fluctuation'][0], expected, rtol=1e-12)
    np.testing.assert_array_equal(result['segments'], [4])
    assert result['usable_scales'] == 1
    assert result['alpha'].shape == (2,)
    assert np.isnan(result['alpha']).all()


def test_dfa_reports_exact_log_curve_fit_statistics():
    x = np.random.default_rng(52).normal(size=(900, 2))
    result = dfa(x)
    logs = np.log(result['scales'])
    for j in range(2):
        y = np.log(result['fluctuation'][:, j])
        linear = np.polyfit(logs, y, 1)
        residual = np.sum((y - np.polyval(linear, logs)) ** 2)
        assert result['alpha'][j] == pytest.approx(linear[0])
        assert result['residual_sse'][j] == pytest.approx(residual)
        assert result['r2'][j] == pytest.approx(1 - residual / np.sum((y-y.mean()) ** 2))
        assert result['curvature'][j] == pytest.approx(np.polyfit(logs, y, 2)[0])


def test_dfa_columns_and_affine_rescaling_do_not_change_exponent():
    x = np.random.default_rng(78).normal(size=900)
    result = dfa(np.column_stack((x, 7*x+13)))
    np.testing.assert_allclose(result['alpha'][0], result['alpha'][1], atol=1e-13)
    np.testing.assert_allclose(result['fluctuation'][:, 1], 7*result['fluctuation'][:, 0])
    assert dfa(x)['fluctuation'].shape == (9, 1)


def test_dfa_zero_rms_is_explicitly_invalid_without_warnings():
    with np.errstate(all='raise'):
        result = dfa(np.full((900, 2), 10 / 3))
        crossed = crossover(result)
        rs = rs_estimate(np.ones(900))
    assert not result['fluctuation'].any()
    for field in ('alpha', 'r2', 'curvature', 'residual_sse'):
        assert np.isnan(result[field]).all()
    assert np.isnan(crossed['improvement']).all()
    assert np.isnan(rs['exponent']).all()


def test_long_synthetic_series_order_persistence_correctly():
    rng = np.random.default_rng(104)
    white = rng.normal(size=32768)
    persistent = np.empty_like(white)
    persistent[0] = white[0]
    for i in range(1, len(white)):
        persistent[i] = .8*persistent[i-1] + white[i]
    anti = np.diff(np.r_[0., white])
    result = dfa(np.column_stack((white, persistent, anti)))
    assert .42 < result['alpha'][0] < .58
    assert result['alpha'][1] > result['alpha'][0] + .15
    assert result['alpha'][2] < result['alpha'][0] - .2
    assert .4 < rs_estimate(white)['exponent'][0] < .75


def test_second_order_detrending_removes_linear_input_trend():
    rng = np.random.default_rng(208)
    x = rng.normal(size=900)
    np.testing.assert_allclose(dfa(x, order=2)['fluctuation'],
                               dfa(x + .25*np.arange(900), order=2)['fluctuation'],
                               rtol=1e-9, atol=1e-9)


def test_continuous_crossover_recovers_known_slopes_and_sse_gain():
    scales = np.array([8, 13, 21, 34, 52, 78, 104, 156, 208])
    logs = np.log(scales)
    y = .2 + .3*logs + .6*np.maximum(0., logs-np.log(52))
    result = crossover(dict(scales=scales, fluctuation=np.exp(y)[:, None]))
    np.testing.assert_array_equal(result['boundaries'], [52, 104, 156])
    assert result['improvement'][0, 0] == pytest.approx(1.)
    assert result['short_alpha'][0, 0] == pytest.approx(.3)
    assert result['long_alpha'][0, 0] == pytest.approx(.9)
    # A knot at 156 has only one scale strictly above it, so is unsupported.
    assert np.isnan(result['improvement'][2, 0])


def test_crossover_requires_two_scales_strictly_on_each_side():
    result = crossover(dict(scales=np.array([13, 26, 52, 104]),
                            fluctuation=np.array([[1.], [2.], [3.], [5.]])),
                       boundaries=(26, 52))
    assert np.isnan(result['improvement']).all()


def test_rs_matches_hand_computed_segment_range_over_std():
    x = np.tile([-1., -1., 1., 1.], 8)
    result = rs_estimate(x, scales=(4, 8))
    np.testing.assert_allclose(result['rs'][:, 0], [2., 2.])
    assert result['exponent'][0] == pytest.approx(0., abs=1e-14)


@pytest.mark.parametrize('x', [[], [[1., 2.]], np.ones((2, 2, 2)), [1., np.nan],
                               [1., np.inf], ['x', 'y'], [1+2j, 3]])
def test_invalid_input_rejected(x):
    # One observation is valid mathematically; a one-row matrix is also valid.
    if np.asarray(x).shape == (1, 2):
        assert dfa(x)['usable_scales'] == 0
        return
    for function in (profile, dfa, rs_estimate):
        with pytest.raises(ValueError):
            function(x)


@pytest.mark.parametrize('scales', [(8, 8), (13, 8), (8., 13.), (0, 8), (True, 8), ()])
def test_bad_scale_grids_rejected(scales):
    with pytest.raises(ValueError):
        supported_scales(100, scales)


@pytest.mark.parametrize('kwargs', [dict(n=0), dict(n=3.5), dict(n=True),
                                  dict(n=100, min_segments=0), dict(n=100, order=-1),
                                  dict(n=100, order=1.5), dict(n=100, scales=(2, 8))])
def test_bad_support_arguments_rejected(kwargs):
    with pytest.raises(ValueError):
        supported_scales(**kwargs)


def test_invalid_crossover_curve_and_knots_rejected():
    curve = dict(scales=np.array([8, 13, 21, 34]), fluctuation=np.ones((4, 1)))
    for boundaries in ((), (52, 52), (-1,), (np.nan,)):
        with pytest.raises(ValueError):
            crossover(curve, boundaries=boundaries)
    with pytest.raises(ValueError):
        crossover(dict(scales=curve['scales'], fluctuation=np.ones((3, 1))))
