"""DFA and reference R/S estimators for finite numeric time series.

These mathematical helpers accept arbitrary synthetic lengths. Historical data
cutoffs belong to the caller's research-data validation, not these estimators.
"""
from functools import lru_cache
from numbers import Integral, Real

import numpy as np


SCALES = (8, 13, 21, 34, 52, 78, 104, 156, 208, 312)


def _integer(value, name, minimum):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)


def _scale_grid(scales, order):
    try:
        values = tuple(scales)
    except TypeError as exc:
        raise ValueError('An ordered, nonempty integer scale grid is required') from exc
    if not values:
        raise ValueError('An ordered, nonempty integer scale grid is required')
    checked = [_integer(s, 'scale', order + 2) for s in values]
    if any(a >= b for a, b in zip(checked, checked[1:])):
        raise ValueError('Scales must be strictly increasing')
    return np.asarray(checked, dtype=int)


def supported_scales(n, scales=SCALES, min_segments=4, order=1):
    """Scales with at least ``min_segments`` forward nonoverlapping blocks.

    Reverse blocks improve coverage but never double the support count. Scales
    must leave at least one residual degree of freedom after detrending.
    """
    n = _integer(n, 'n', 1)
    min_segments = _integer(min_segments, 'min_segments', 1)
    order = _integer(order, 'order', 0)
    grid = _scale_grid(scales, order)
    return grid[n // grid >= min_segments]


def _matrix(x):
    try:
        raw = np.asarray(x)
        if np.iscomplexobj(raw):
            raise ValueError('Real numeric observations are required')
        values = np.asarray(raw, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError('Real numeric observations are required') from exc
    if values.ndim not in (1, 2) or values.shape[0] == 0 or values.size == 0:
        raise ValueError('A nonempty vector or time-by-series matrix is required')
    if not np.isfinite(values).all():
        raise ValueError('Observations must be finite')
    return values[:, None] if values.ndim == 1 else values


def _center(values):
    # Subtracting an observed origin first preserves exactly constant columns,
    # including non-binary-representable constants such as 10/3.
    shifted = values - values[0]
    return shifted - shifted.mean(axis=0)


def profile(x):
    """Demean each series and cumulatively sum along time; preserve 1D/2D."""
    values = _matrix(x)
    integrated = np.cumsum(_center(values), axis=0)
    return integrated[:, 0] if np.asarray(x).ndim == 1 else integrated


@lru_cache(maxsize=128)
def _detrend_basis(scale, order):
    """Cached orthonormal polynomial projector factors (avoids dense s-by-s)."""
    t = np.linspace(-1., 1., scale)
    basis = np.linalg.qr(np.vander(t, N=order + 1, increasing=True), mode='reduced')[0]
    basis.setflags(write=False)
    return basis


def _blocks(values, scale):
    n, columns = values.shape
    count = n // scale
    forward = values[:count * scale].reshape(count, scale, columns)
    reverse = values[n - count * scale:].reshape(count, scale, columns)
    return np.concatenate((forward, reverse), axis=0)


def _log_fits(scales, fluctuation):
    """Vectorized masked linear fits and quadratic curvature on log scales."""
    columns = fluctuation.shape[1]
    answer = {key: np.full(columns, np.nan) for key in
              ('alpha', 'r2', 'curvature', 'residual_sse')}
    if len(scales) < 2:
        return answer
    t = np.log(scales)[:, None]
    valid = np.isfinite(fluctuation) & (fluctuation > 0)
    logs = np.zeros_like(fluctuation)
    np.log(fluctuation, out=logs, where=valid)
    count = valid.sum(axis=0)
    denominator = np.maximum(count, 1)
    mean_t = (t * valid).sum(axis=0) / denominator
    mean_y = logs.sum(axis=0) / denominator
    centered_t = t - mean_t
    centered_y = logs - mean_y
    ss_t = (centered_t**2 * valid).sum(axis=0)
    fit = (count >= 2) & (ss_t > 0)
    alpha = np.full(columns, np.nan)
    np.divide((centered_t * centered_y * valid).sum(axis=0), ss_t,
              out=alpha, where=fit)
    answer['alpha'] = alpha
    residual = centered_y - centered_t * np.where(fit, alpha, 0.)
    sse = (residual**2 * valid).sum(axis=0)
    answer['residual_sse'][fit] = sse[fit]
    ss_y = (centered_y**2 * valid).sum(axis=0)
    rfit = fit & (ss_y > 0)
    answer['r2'][rfit] = 1. - sse[rfit] / ss_y[rfit]
    # Most searches have complete curves: solve all columns with one factorization.
    full = valid.all(axis=0) & (count >= 3)
    if full.any():
        x = t[:, 0] - t[:, 0].mean()
        design = np.column_stack((np.ones(len(x)), x, x*x))
        answer['curvature'][full] = np.linalg.lstsq(design, logs[:, full], rcond=None)[0][2]
    for column in np.flatnonzero((count >= 3) & ~full):
        keep = valid[:, column]
        x = t[keep, 0] - t[keep, 0].mean()
        answer['curvature'][column] = np.linalg.lstsq(
            np.column_stack((np.ones(len(x)), x, x*x)), logs[keep, column], rcond=None)[0][2]
    return answer


def dfa(x, scales=SCALES, order=1):
    """DFA RMS pooled over forward and reverse nonoverlapping segmentations.

    ``fluctuation`` always has shape (supported scales, series), including 1D
    input. ``segments`` counts each orientation separately, not their sum.
    Invalid/zero-RMS curves have NaN exponents and fit diagnostics. Quadratic
    curvature is the coefficient of log(scale)**2, requiring at least 3 scales.
    """
    values = _matrix(x)
    order = _integer(order, 'order', 0)
    grid = supported_scales(len(values), scales, order=order)
    integrated = np.cumsum(_center(values), axis=0)
    fluctuation = np.empty((len(grid), values.shape[1]))
    for i, scale in enumerate(grid):
        blocks = _blocks(integrated, int(scale))
        basis = _detrend_basis(int(scale), order)
        coefficients = np.einsum('sd,ksm->kdm', basis, blocks, optimize=True)
        residual = blocks - np.einsum('sd,kdm->ksm', basis, coefficients, optimize=True)
        fluctuation[i] = np.sqrt(np.mean(residual * residual, axis=(0, 1)))
    return dict(scales=grid, fluctuation=fluctuation, usable_scales=len(grid),
                segments=len(values) // grid, **_log_fits(grid, fluctuation))


def crossover(curve, boundaries=(52, 104, 156)):
    """Continuous hinge log-log fits with two scales strictly on each side.

    A scale equal to the boundary participates in the fit but counts toward
    neither side's support. Improvement is (linear SSE - hinge SSE)/linear SSE;
    a numerically exact linear curve has zero improvement, and missing support
    or a zero-RMS curve yields NaN. Slopes are fitted jointly for continuity.
    """
    try:
        knots = tuple(boundaries)
    except TypeError as exc:
        raise ValueError('Ordered positive finite crossover boundaries required') from exc
    if (not knots or any(isinstance(b, (bool, np.bool_)) or not isinstance(b, Real)
                         or not np.isfinite(b) or b <= 0 for b in knots)
            or any(a >= b for a, b in zip(knots, knots[1:]))):
        raise ValueError('Ordered positive finite crossover boundaries required')
    try:
        grid = np.asarray(curve['scales'])
        fluctuation = np.asarray(curve['fluctuation'], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('A DFA scales/fluctuation curve is required') from exc
    if grid.ndim != 1:
        raise ValueError('Curve scales must be one-dimensional')
    if len(grid):
        grid = _scale_grid(grid, 0)
    if fluctuation.ndim == 1:
        fluctuation = fluctuation[:, None]
    if (fluctuation.ndim != 2 or fluctuation.shape[0] != len(grid)
            or fluctuation.shape[1] < 1 or np.isinf(fluctuation).any()
            or (fluctuation < 0).any()):
        raise ValueError('Curve dimensions and nonnegative fluctuations must agree')
    shape = (len(knots), fluctuation.shape[1])
    answer = {name: np.full(shape, np.nan) for name in
              ('improvement', 'short_alpha', 'long_alpha')}
    answer['boundaries'] = np.asarray(knots)
    if len(grid) < 4:
        return answer
    for i, knot in enumerate(knots):
        if (grid < knot).sum() < 2 or (grid > knot).sum() < 2:
            continue
        valid = np.isfinite(fluctuation) & (fluctuation > 0)
        # Group equal masks: normal full-curve searches require one solve/knot.
        masks, inverse = np.unique(valid.T, axis=0, return_inverse=True)
        for group, keep in enumerate(masks):
            if ((grid < knot) & keep).sum() < 2 or ((grid > knot) & keep).sum() < 2:
                continue
            columns = np.flatnonzero(inverse == group)
            t = np.log(grid[keep]) - np.log(knot)
            y = np.log(fluctuation[np.ix_(keep, columns)])
            linear = np.column_stack((np.ones(len(t)), t))
            hinge = np.column_stack((linear, np.maximum(t, 0.)))
            base = np.linalg.lstsq(linear, y, rcond=None)[0]
            fitted = np.linalg.lstsq(hinge, y, rcond=None)[0]
            base_sse = ((y - linear @ base)**2).sum(axis=0)
            hinge_sse = ((y - hinge @ fitted)**2).sum(axis=0)
            improvement = np.zeros(len(columns))
            meaningful = base_sse > np.finfo(float).eps * np.maximum(1., (y*y).sum(axis=0))
            improvement[meaningful] = np.clip(
                1. - hinge_sse[meaningful] / base_sse[meaningful], 0., 1.)
            answer['improvement'][i, columns] = improvement
            answer['short_alpha'][i, columns] = fitted[1]
            answer['long_alpha'][i, columns] = fitted[1] + fitted[2]
    return answer


def rs_estimate(x, scales=SCALES):
    """Reference mean segment R/S and its log-log slope, using the DFA support.

    Segment standard deviations use ddof=0; constant segments are omitted. Both
    endpoint segmentations contribute equally, including at divisible lengths.
    """
    values = _matrix(x)
    grid = supported_scales(len(values), scales, order=0)
    estimates = np.full((len(grid), values.shape[1]), np.nan)
    for i, scale in enumerate(grid):
        blocks = _blocks(values, int(scale))
        shifted = blocks - blocks[:, :1]
        centered = shifted - shifted.mean(axis=1, keepdims=True)
        cumulative = np.cumsum(centered, axis=1)
        ranges = np.ptp(cumulative, axis=1)
        std = np.sqrt(np.mean(centered * centered, axis=1))
        valid = std > 0
        ratios = np.zeros_like(std)
        np.divide(ranges, std, out=ratios, where=valid)
        counts = valid.sum(axis=0)
        np.divide(ratios.sum(axis=0), counts, out=estimates[i], where=counts > 0)
    return dict(scales=grid, rs=estimates, exponent=_log_fits(grid, estimates)['alpha'])
