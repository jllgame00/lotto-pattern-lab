"""Frozen H20 representations and secondary long-memory diagnostics.

Research builders require an exact prefix ending by draw 1245. Mathematical
helpers also accept long synthetic series for independent estimator checks.
"""
import hashlib
from numbers import Integral

import numpy as np

from .change_point_representation import shape_vector
from .recurrence import research_matrix


SHAPE_NAMES = ('sum', 'range', 'std', 'spacing_std', 'odd_count')
BLOCKS = (1, 2, 4, 8, 13, 26, 52)
WINDOWS = (312, 416, 624)


def build_series(x, *, cutoff=None):
    """Return 45 centered appearances, five frozen shapes, and five bands.

    Each output row corresponds to the same completed draw as its input row.
    ``cutoff`` verifies the supplied prefix; it never truncates future rows.
    """
    x = research_matrix(x)
    n = len(x)
    if cutoff is not None and (
        isinstance(cutoff, (bool, np.bool_))
        or not isinstance(cutoff, Integral) or cutoff != n
    ):
        raise ValueError('cutoff must equal the supplied exact prefix length')
    values = np.column_stack((
        x.astype(float) - 6 / 45,
        shape_vector(x)[:, [0, 1, 2, 4, 6]],
        x.reshape(n, 5, 9).sum(axis=2),
    )).astype(np.float64)
    names = ([f'number_{i:02d}' for i in range(1, 46)]
             + [f'shape_{name}' for name in SHAPE_NAMES]
             + [f'band_{i:02d}_{i+8:02d}' for i in range(1, 46, 9)])
    return dict(values=values, names=names,
                groups=['number'] * 45 + ['shape'] * 5 + ['band'] * 5,
                cutoff=n, representation_hash=hashlib.sha256(values.tobytes()).hexdigest())


def _matrix(x):
    """Normalize finite generic mathematical input to time by column."""
    x = np.asarray(x, dtype=float)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or not x.shape[0] or not x.shape[1] or not np.isfinite(x).all():
        raise ValueError('A nonempty finite one- or two-dimensional series is required')
    return x


def _log_fit(coordinate, values):
    """Fit each positive ordinate column, leaving unsupported fits undefined."""
    slope = np.full(values.shape[1], np.nan)
    r2 = slope.copy()
    log_coordinate = np.log(coordinate)
    for j in range(values.shape[1]):
        valid = np.isfinite(values[:, j]) & (values[:, j] > 0)
        if valid.sum() < 2:
            continue
        a = log_coordinate[valid]
        y = np.log(values[valid, j])
        centered = a - a.mean()
        slope[j] = centered @ (y - y.mean()) / (centered @ centered)
        residual = y - y.mean() - slope[j] * centered
        total = np.sum((y - y.mean()) ** 2)
        if total > 0:
            r2[j] = 1 - np.sum(residual ** 2) / total
    return slope, r2


def aggregation(x, blocks=BLOCKS):
    """Fit log variance of disjoint block means against log block size.

    Retain only block sizes with at least four independent complete blocks.
    Variance uses ``ddof=1``; incomplete tails are omitted at each size. All
    fit outputs have one entry per input column, including for 1D inputs.
    Constant columns have zero variances and undefined slope/deviation/R².
    """
    x = _matrix(x)
    blocks = tuple(blocks)
    if (not blocks or any(isinstance(b, (bool, np.bool_))
                          or not isinstance(b, Integral) or b < 1 for b in blocks)
            or len(set(blocks)) != len(blocks)):
        raise ValueError('Distinct positive integer block sizes are required')
    supported = np.array(sorted(b for b in blocks if len(x) // b >= 4), dtype=int)
    if len(supported) < 2:
        raise ValueError('At least two block sizes with four complete blocks are required')
    counts = len(x) // supported
    # Subtract an exact observed origin before averaging: repeated irrational
    # constants otherwise acquire tiny nonzero variance from mean roundoff.
    x = x - x[0]
    variance = np.stack([
        x[:count * block].reshape(count, block, x.shape[1]).mean(axis=1).var(axis=0, ddof=1)
        for block, count in zip(supported, counts)
    ])
    slope, r2 = _log_fit(supported, variance)
    return dict(slope=slope, deviation=np.abs(slope + 1), r2=r2,
                blocks=supported, variance=variance, n_blocks=counts)


def spectral_slope(x):
    """Secondary periodogram beta, using fixed Fourier indices 2..floor(N/26).

    ``beta`` is minus the log-power/log-frequency slope, so white noise has
    beta near zero. Power is ``abs(rfft(x-mean))**2/N`` without a one-sided
    doubling factor. Frequency/power include only the fixed fitted band.
    """
    x = _matrix(x)
    indices = np.arange(2, len(x) // 26 + 1, dtype=int)
    if len(indices) < 2:
        raise ValueError('At least two fixed low-frequency bins are required (N >= 78)')
    frequency = indices / len(x)
    x = x - x[0]
    power = np.abs(np.fft.rfft(x - x.mean(axis=0), axis=0)[indices]) ** 2 / len(x)
    slope, r2 = _log_fit(frequency, power)
    return dict(beta=-slope, r2=r2, bins=len(indices), frequency=frequency, power=power)


def rolling_endpoints(n, window, stride=52):
    """Return all complete-window endpoints and include the exact final draw."""
    if (isinstance(n, (bool, np.bool_)) or not isinstance(n, Integral)
            or not 2 <= n <= 1245 or window not in WINDOWS
            or isinstance(window, (bool, np.bool_)) or not isinstance(window, Integral)
            or n < window or isinstance(stride, (bool, np.bool_))
            or not isinstance(stride, Integral) or stride < 1):
        raise ValueError('Require a supported window, valid research cutoff, and positive stride')
    endpoints = np.arange(window, n + 1, stride, dtype=int)
    if endpoints[-1] != n:
        endpoints = np.append(endpoints, n)
    return endpoints


def rolling_series(x, window, end):
    """Build the completed window ending at one-based ``end`` from valid input.

    The entire supplied input is validated before slicing, so future research
    draw 1246 cannot enter this helper even when ``end`` is earlier.
    """
    x = research_matrix(x)
    rolling_endpoints(len(x), window)
    if (isinstance(end, (bool, np.bool_)) or not isinstance(end, Integral)
            or not window <= end <= len(x)):
        raise ValueError('end must identify a completed supported window within input')
    result = build_series(x[end - window:end])
    result.update(cutoff=int(end), start_draw=int(end - window + 1), window=int(window))
    return result
