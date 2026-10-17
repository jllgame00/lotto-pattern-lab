"""Phase 18 fixed-center reflection statistics for historical research prefixes.

Number labels are one-based. A positive lag aligns a source at t with a target
at t+lag; rolling activity includes its completed endpoint. Working z scores
are descriptive binomial diagnostics, never independent-event p values.
"""
from math import comb
from numbers import Integral

import numpy as np

from .recurrence import research_matrix


LAGS = (0, 1, 2, 3, 4, 8, 13, 26, 52)
ACTIVITY_WINDOWS = (10, 26, 52)
REGIME_WINDOWS = (26, 52, 104)
SHIFTS = (-4, -2, 0, 2, 4)
_LOW = np.arange(22)
_HIGH = 44 - _LOW
_SOURCE = np.column_stack((_LOW, _HIGH)).ravel()
_TARGET = 44 - _SOURCE


def _integer(value):
    return isinstance(value, Integral) and not isinstance(value, (bool, np.bool_))


def mirror(n):
    """Reflect exact integer labels 1..45 around 23, preserving array shape."""
    # Preserve Python boolean/float types in mixed lists before NumPy coercion.
    values = np.asarray(n, dtype=object)
    if (not all(_integer(value) for value in values.flat) or np.any(values < 1)
            or np.any(values > 45)):
        raise ValueError('Mirror requires exact integer number labels in 1..45')
    # Cast after bounds checks so small unsigned input types cannot underflow.
    result = 46 - values.astype(np.int64)
    return int(result) if values.ndim == 0 else result


def reflection_shift(n, shift):
    """Return 46-n+shift, or None outside 1..45; never wrap or clip."""
    if not _integer(n) or not 1 <= n <= 45:
        raise ValueError('Source number must be an exact integer in 1..45')
    if not _integer(shift) or shift not in SHIFTS:
        raise ValueError('Shift must be predeclared')
    target = int(46 - n + shift)
    return target if 1 <= target <= 45 else None


def _aligned(x, lag):
    x = research_matrix(x)
    if not _integer(lag) or lag not in LAGS or lag >= len(x):
        raise ValueError('Lag must be predeclared and leave an aligned draw')
    return (x, x) if lag == 0 else (x[:-lag], x[lag:])


def draw_metrics(x):
    """Per-draw complete mirror pairs, center, Jaccard and side balance."""
    x = research_matrix(x)
    pairs = (x[:, _LOW] & x[:, _HIGH]).sum(axis=1)
    center = x[:, 22].astype(np.int64)
    paired_numbers = 2 * pairs
    intersection = paired_numbers + center
    left, right = x[:, :22].sum(axis=1), x[:, 23:].sum(axis=1)
    return dict(pairs=pairs, paired_numbers=paired_numbers, center=center,
                symmetry=paired_numbers / (6 - center),
                jaccard=intersection / (12 - intersection),
                left=left, right=right, imbalance=np.abs(left - right))


def exact_distribution():
    """Exact IID joint probability of complete-pair count and center presence."""
    denominator = comb(45, 6)
    result = []
    for pairs in range(4):
        for center in (0, 1):
            singles = 6 - 2 * pairs - center
            if 0 <= singles <= 22 - pairs:
                probability = (comb(22, pairs) * comb(22-pairs, singles)
                               * 2**singles / denominator)
                result.append(dict(pairs=pairs, center=center, probability=probability))
    return result


def _divide(numerator, denominator):
    numerator, denominator = np.broadcast_arrays(numerator, denominator)
    return np.divide(numerator, denominator,
                     out=np.full(numerator.shape, np.nan), where=denominator > 0)


def pooled_relation(x, lag, shift=0):
    """Pool mapped source events, excluding 23, fixed points and boundary loss.

    ``sources`` counts source-number events; ``draws``/``sample_count`` count
    aligned draws. Per-draw event/hit counts support dependent-data resampling.
    The lag-zero conditional IID baseline is 5/44; positive lags use 6/45.
    """
    source, target = _aligned(x, lag)
    if not _integer(shift) or shift not in SHIFTS:
        raise ValueError('Shift must be predeclared')
    labels = np.arange(1, 46)
    mapped = 46 - labels + shift
    valid = (labels != 23) & (mapped >= 1) & (mapped <= 45) & (mapped != labels)
    events = source[:, valid]
    successes = events & target[:, mapped[valid]-1]
    event_counts, hit_counts = events.sum(axis=1), successes.sum(axis=1)
    sources, hits = int(event_counts.sum()), int(hit_counts.sum())
    baseline = 5/44 if lag == 0 else 6/45
    rate = hits / sources if sources else float('nan')
    z = ((hits - sources * baseline) / np.sqrt(sources * baseline * (1-baseline))
         if sources else float('nan'))
    return dict(sources=sources, hits=hits, rate=rate, expected_rate=baseline,
                lift=rate / baseline, risk_difference=rate-baseline,
                working_z=float(z), draws=len(source), sample_count=len(source),
                event_counts=event_counts, hit_counts=hit_counts)


def pair_relations(x, lag, minimum_support=20):
    """44 directional relations in interleaved low/high pair order.

    Rows are 1->45,45->1,2->44,44->2,...,22->24,24->22. Positive-lag
    baselines are the target's mean over aligned future rows. Eligibility is
    defined by observed source support, without significance screening.
    """
    source, target = _aligned(x, lag)
    if not _integer(minimum_support) or minimum_support < 1:
        raise ValueError('Minimum support must be a positive exact integer')
    events, outcomes = source[:, _SOURCE], target[:, _TARGET]
    support = events.sum(axis=0)
    hits = (events & outcomes).sum(axis=0)
    rate = _divide(hits, support)
    baseline = np.full(44, 5/44) if lag == 0 else outcomes.mean(axis=0)
    difference = rate - baseline
    z = _divide(hits-support*baseline, np.sqrt(support*baseline*(1-baseline)))
    return dict(source=_SOURCE+1, target=_TARGET+1, support=support,
                hits=hits, rate=rate, baseline=baseline, risk_difference=difference,
                lift=_divide(rate, baseline), working_z=z,
                eligible=(support >= minimum_support))


def _rolling_rates(x, window):
    cumulative = np.vstack((np.zeros((1, 45), dtype=np.int64),
                            np.cumsum(x, axis=0, dtype=np.int64)))
    return (cumulative[window:] - cumulative[:-window]) / window


def activity(x, window, cutoff=None):
    """Latest completed activity; cutoff certifies and never truncates a prefix."""
    x = research_matrix(x)
    if (not _integer(window) or window not in ACTIVITY_WINDOWS
            or window > len(x)):
        raise ValueError('Activity window must be predeclared and fully observed')
    if cutoff is not None and (not _integer(cutoff) or cutoff != len(x)):
        raise ValueError('Cutoff must exactly match the supplied research prefix')
    own = x[-window:].mean(axis=0)
    reflected = own[::-1].copy()
    return dict(own=own, mirror=reflected, difference=reflected-own, sum=own+reflected)


def _correlations(a, b, minimum_samples=26):
    """Columnwise Pearson correlations, with constants and short samples NaN."""
    if len(a) < minimum_samples:
        return np.full(a.shape[1], np.nan)
    ac, bc = a-a.mean(axis=0), b-b.mean(axis=0)
    denominator = np.sqrt(np.square(ac).sum(axis=0) * np.square(bc).sum(axis=0))
    valid = (np.ptp(a, axis=0) > 0) & (np.ptp(b, axis=0) > 0)
    return np.divide((ac*bc).sum(axis=0), denominator,
                     out=np.full(a.shape[1], np.nan), where=valid & (denominator > 0))


def activity_correlations(x):
    """Fixed 1122 rolling-activity cells: 22 pairs x 3 windows x 17 directions.

    Order is window, lag, pair, direction. Lag zero has low_to_high only;
    positive lags include both directions. Each rate window includes t and
    source rates at t align with target rates at t+lag. At least 26 aligned
    completed rate points and variable series are needed for eligibility.
    """
    x = research_matrix(x)
    result = []
    for window in ACTIVITY_WINDOWS:
        rates = _rolling_rates(x, window) if len(x) >= window else np.empty((0, 45))
        for lag in LAGS:
            directions = ('low_to_high',) if lag == 0 else ('low_to_high', 'high_to_low')
            samples = max(0, len(rates)-lag)
            source = rates[:samples, _LOW]
            target = rates[lag:lag+samples, _HIGH]
            forward = _correlations(source, target)
            reverse = (_correlations(rates[:samples, _HIGH], rates[lag:lag+samples, _LOW])
                       if lag else None)
            for pair in range(22):
                for direction in directions:
                    value = forward[pair] if direction == 'low_to_high' else reverse[pair]
                    result.append(dict(pair=pair+1, low=pair+1, high=45-pair,
                                       window=window, lag=lag, direction=direction,
                                       correlation=float(value), samples=samples,
                                       eligible=bool(np.isfinite(value))))
    return result


def rolling_symmetry(x):
    """Regime summaries at one-based W,W+26,... and the final endpoint.

    Mean binary correlation includes only variable mirror pairs and requires
    at least twelve such pairs; constant pairs never acquire artificial zeros.
    """
    x = research_matrix(x)
    metrics = draw_metrics(x)
    means = {name: np.r_[0., np.cumsum(metrics[name], dtype=float)]
             for name in ('pairs', 'symmetry', 'imbalance')}
    low, high = x[:, _LOW].astype(np.int64), x[:, _HIGH].astype(np.int64)
    counts = [np.vstack((np.zeros((1, 22), dtype=np.int64), np.cumsum(data, axis=0)))
              for data in (low, high, low*high)]
    result = []
    for window in REGIME_WINDOWS:
        if len(x) < window:
            continue
        endpoints = sorted(set(range(window, len(x)+1, 26)) | {len(x)})
        for endpoint in endpoints:
            start = endpoint-window
            a, b, joint = [c[endpoint]-c[start] for c in counts]
            denominator = np.sqrt(a*(window-a)*b*(window-b))
            corr = _divide(window*joint-a*b, denominator)
            valid_pairs = int(np.isfinite(corr).sum())
            row = dict(window=window, endpoint=endpoint, valid_pairs=valid_pairs,
                       mean_correlation=float(np.nanmean(corr)) if valid_pairs >= 12 else float('nan'))
            row.update({f'mean_{name}': float((c[endpoint]-c[start])/window)
                        for name, c in means.items()})
            result.append(row)
    return result
