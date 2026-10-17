"""Descriptive Morlet power and localized regions, never predictive probabilities.

Series are centered and divided by their population standard deviation. Thus
sparse binary indicators retain standardized rare-event amplitudes: a large
power value can reflect a few events rather than a stable oscillation. Thresholds
are descriptive and need empirical null calibration, including the region search.
"""
from numbers import Real

import numpy as np
from scipy.ndimage import label
from scipy.signal import fftconvolve


PERIODS = (8, 13, 20, 26, 39, 52, 78, 104)
_W0 = 6.0
_FOURIER_FACTOR = 4 * np.pi / (_W0 + np.sqrt(2 + _W0 ** 2))


def morlet_transform(values, periods=PERIODS):
    """Transform finite time-by-series values with unit-L2 complex Morlet kernels.

    One-dimensional input is one series. Periods must be distinct numeric values
    in [4, N/4]; output scales are sorted by increasing period. Coefficients and
    power have shape (series, scale, time), and ``valid`` has shape (scale, time).
    The zero-padded convolution is marked invalid within sqrt(2)*scale samples
    of either edge (the power e-folding cone of influence). Kernels extend to
    eight scales on each side and include the admissibility correction.

    Constant series yield zero coefficients. Global power is the mean over
    valid times at each scale; concentration therefore compares scale means,
    not unequal numbers of supported time points. This is not a probability.
    """
    try:
        x = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError('values must be finite numeric time-by-series data') from exc
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or min(x.shape) == 0 or not np.isfinite(x).all():
        raise ValueError('values must be nonempty finite time-by-series data')
    raw_periods = np.asarray(periods, dtype=object)
    if (raw_periods.ndim != 1 or raw_periods.size == 0
            or any(isinstance(p, (bool, np.bool_)) or not isinstance(p, Real)
                   for p in raw_periods)):
        raise ValueError('periods must be a nonempty numeric sequence')
    periods = np.sort(raw_periods.astype(float))
    if (not np.isfinite(periods).all() or np.any(periods < 4)
            or np.any(periods > len(x) / 4) or np.any(np.diff(periods) == 0)):
        raise ValueError('periods must be distinct finite values between 4 and N/4')
    mean, std = x.mean(axis=0), x.std(axis=0)
    # Repeated noninteger constants can acquire nonzero std through mean roundoff.
    std = np.where(np.ptp(x, axis=0) == 0, 0., std)
    standardized = np.divide(x - mean, std, out=np.zeros_like(x), where=std > 0)
    scales = periods / _FOURIER_FACTOR
    coefficients = np.empty((x.shape[1], len(scales), len(x)), dtype=complex)
    for index, scale in enumerate(scales):
        radius = int(np.ceil(8 * scale))
        u = np.arange(-radius, radius + 1) / scale
        kernel = (np.exp(1j * _W0 * u) - np.exp(-_W0 ** 2 / 2)) * np.exp(-u ** 2 / 2)
        kernel /= np.sqrt(np.sum(np.abs(kernel) ** 2))
        coefficients[:, index, :] = fftconvolve(
            standardized.T, np.conjugate(kernel[::-1])[None, :], mode='same', axes=1)
    power = np.abs(coefficients) ** 2
    distance = np.minimum(np.arange(len(x)), np.arange(len(x))[::-1])
    valid = distance[None, :] >= np.sqrt(2) * scales[:, None]
    global_power, dominant = _power_summaries(power, valid, periods)
    return dict(coefficients=coefficients, power=power, valid=valid,
                periods=periods, scale=scales, global_power=global_power,
                dominant_period_by_time=dominant,
                normalization=dict(mean=mean, std=std, ddof=0,
                                   method='centered_population_standard_deviation',
                                   kernel='unit_l2', constant_series=std == 0))


def _power_summaries(power, valid, periods):
    global_power = np.sum(np.where(valid[None, :, :], power, 0), axis=2) / valid.sum(axis=1)
    supported = np.where(valid[None, :, :], power, -np.inf)
    strongest = supported.max(axis=1)
    dominant = periods[supported.argmax(axis=1)].astype(float)
    dominant[~np.isfinite(strongest) | (strongest <= 0)] = np.nan
    return global_power, dominant


def _summary_arguments(transform, names, min_cycles, threshold):
    for name, value, lower in [('min_cycles', min_cycles, 2), ('threshold', threshold, 0)]:
        if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
                or not np.isfinite(value) or value < lower
                or (name == 'threshold' and value == 0)):
            raise ValueError(f'{name} must be finite and {">" if lower == 0 else ">="} {lower}')
    count = transform['power'].shape[0]
    if names is None:
        return [f'series_{i + 1}' for i in range(count)]
    if isinstance(names, str) or len(names) != count:
        raise ValueError('names must provide one name per series')
    return [str(name) for name in names]


def localized_regions(transform, names=None, min_cycles=2, threshold=4.):
    """Find threshold-exceeding connected scale/time regions inside the cone.

    Four-neighbor adjacency links only immediately neighboring scales or times.
    Each region must span ceil(min_cycles * representative_period) consecutive
    times. Its representative scale has the greatest integrated excess power;
    score is total excess above threshold divided by sqrt(number of cells).
    Stability is the fraction of region times whose strongest excess is at that
    representative scale. Bounds are inclusive, ONE-based sample positions.
    Scale spacing, threshold and component geometry affect all these summaries.
    """
    names = _summary_arguments(transform, names, min_cycles, threshold)
    power, valid, periods = (transform[key] for key in ('power', 'valid', 'periods'))
    regions = []
    for series_index, series_power in enumerate(power):
        components, count = label(valid & (series_power > threshold))
        for component in range(1, count + 1):
            mask = components == component
            _, times = np.nonzero(mask)
            start, end = int(times.min()), int(times.max())
            excess = np.where(mask, np.maximum(series_power - threshold, 0), 0)
            representative = int(excess.sum(axis=1).argmax())
            period = float(periods[representative])
            duration = end - start + 1
            if duration < int(np.ceil(min_cycles * period)):
                continue
            ridge = excess[:, start:end + 1].argmax(axis=0)
            regions.append(dict(series=series_index, name=names[series_index],
                                start=start + 1, end=end + 1, period=period,
                                score=float(excess.sum() / np.sqrt(len(times))),
                                duration=duration,
                                scale_stability=float(np.mean(ridge == representative)),
                                max_power=float(series_power[mask].max()),
                                cell_count=int(len(times))))
    return sorted(regions, key=lambda row: (-row['score'], row['series'], row['start'], row['period']))


def summarize_wavelet(transform, names=None, min_cycles=2, threshold=4.):
    """Return compact JSON-safe series summaries; unsupported dominance is null.

    Dominant period is selected by greatest valid-time average power, and global
    concentration is max(global_power)/sum(global_power). Power at a single
    time is not gated by the region duration criterion; region metrics are.
    """
    names = _summary_arguments(transform, names, min_cycles, threshold)
    power, valid, periods = (transform[key] for key in ('power', 'valid', 'periods'))
    global_power, _ = _power_summaries(power, valid, periods)
    regions = localized_regions(transform, names, min_cycles, threshold)
    rows = []
    for index, scale_power in enumerate(global_power):
        total = float(scale_power.sum())
        series_regions = [row for row in regions if row['series'] == index]
        rows.append(dict(series=index, name=names[index],
                         max_localized_power=float(power[index][valid].max()),
                         global_concentration=float(scale_power.max() / total) if total > 0 else 0.,
                         dominant_period=float(periods[scale_power.argmax()]) if total > 0 else None,
                         global_power=scale_power.tolist(), periods=periods.tolist(),
                         region_count=len(series_regions),
                         best_region=series_regions[0] if series_regions else None))
    return rows
