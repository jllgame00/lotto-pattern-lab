"""Exact one-dimensional OT. Draw endpoints are one-based, vectors zero-based.

Signed movement follows order statistics, never identities of lottery balls.
Average quantiles define the W2 barycenter; a W1 barycenter uses medians.
"""
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from .recurrence import research_matrix

LAGS = (1, 2, 3, 4, 8, 13, 26)
ROLLING_WINDOWS = (26, 52, 104)
STEPS = (1, 4, 13, 26)
BARYCENTER_WINDOWS = (10, 26, 52)


def sorted_draws(draws):
    a = np.asarray(draws, float)
    if a.ndim not in (1, 2) or a.shape[-1] != 6 or not np.isfinite(a).all():
        raise ValueError('Six finite number positions required')
    a = np.sort(a, axis=-1)
    if np.any(a < 1) or np.any(a > 45) or np.any(np.diff(a, axis=-1) <= 0) or np.any(a != np.floor(a)):
        raise ValueError('Six distinct integer main numbers in1..45 required')
    return a


def draw_positions(x):
    x = research_matrix(x)
    return (np.nonzero(x)[1] + 1).reshape(-1, 6).astype(float)


def empirical_measure(draw):
    a = sorted_draws(draw)
    if a.ndim != 1:
        raise ValueError('One draw required')
    return a, np.full(6, 1 / 6)


def monotone_matching(a, b):
    return np.column_stack((empirical_measure(a)[0], empirical_measure(b)[0]))


def transport_vector(a, b):
    return sorted_draws(b) - sorted_draws(a)


def quantile_distance(a, b, p=1):
    if p not in (1, 2):
        raise ValueError('Only exact W1/W2 are predeclared')
    return np.mean(np.abs(np.asarray(b) - np.asarray(a)) ** p, axis=-1) ** (1 / p)


def wasserstein(a, b, p=1):
    return quantile_distance(sorted_draws(a), sorted_draws(b), p)


def displacement_summary(d):
    d = np.asarray(d, float)
    return dict(signed=np.mean(d, axis=-1), absolute=np.mean(abs(d), axis=-1),
                rms=np.sqrt(np.mean(d ** 2, axis=-1)), variance=np.var(d, axis=-1),
                positive=np.mean(d > 0, axis=-1), negative=np.mean(d < 0, axis=-1),
                sign_consistency=abs(np.mean(np.sign(d), axis=-1)),
                center_of_mass_change=np.mean(d, axis=-1))


def lag_distances(draws, lag, p=1):
    a = sorted_draws(draws)
    if type(lag) is not int or not 1 <= lag < len(a):
        raise ValueError('Lag outside complete draws')
    return quantile_distance(a[:-lag], a[lag:], p)


def direction(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    dot = np.sum(a * b, axis=-1)
    norm = np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1)
    energy = .5 * (np.sum(a * a, axis=-1) + np.sum(b * b, axis=-1))
    # A zero vector has neutral directional similarity. Tied zeros agree in sign.
    return dict(cosine=np.clip(np.divide(dot, norm, out=np.zeros_like(dot), where=norm > 0), -1, 1),
                normalized_dot=np.divide(dot, energy, out=np.zeros_like(dot), where=energy > 0),
                mean_sign=(np.sign(a.mean(-1)) == np.sign(b.mean(-1))).astype(float),
                coordinate_sign=np.mean(np.sign(a) == np.sign(b), axis=-1))


def acceleration(d):
    return np.diff(np.asarray(d, float), axis=0)


def correlation(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return 0.
    return float(spearmanr(a, b).statistic)


def vector_distances(a, b, metric, scale=None):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if metric == 'euclidean':
        if scale is None:
            scale = np.vstack((a, b)).std(0)
        scale = np.where(np.asarray(scale) > 1e-12, scale, 1.)
        return cdist(a / scale, b / scale) / np.sqrt(6)
    if metric != 'cosine':
        raise ValueError('Predeclared standardized Euclidean or cosine required')
    an, bn = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1)
    out = np.clip(np.nan_to_num(cdist(a, b, 'cosine'), nan=1.), 0, 2)
    out[np.ix_(an == 0, bn == 0)] = 0
    return out


def successor_diagnostic(d, metric):
    d = np.asarray(d, float)
    if len(d) < 5:
        raise ValueError('At least five transport events required')
    # Each selected block includes d_i AND d_(i+1), thus three underlying draws.
    events = np.arange(0, len(d) - 1, 3)
    ii, jj = np.triu_indices(len(events), 1)
    scale = d.std(0)
    distances = vector_distances(d[:-1], d[:-1], metric, scale)
    pair_x = distances[events[ii], events[jj]]
    first, second = d[events[ii] + 1], d[events[jj] + 1]
    pair_cos = direction(first, second)['cosine']
    pair_next = np.sqrt(np.mean((first - second) ** 2, axis=1))
    query = np.arange(3, len(d) - 1)
    past = distances[query].copy()
    past[np.arange(len(d) - 1)[None, :] > query[:, None] - 3] = np.inf
    nearest = np.argmin(past, axis=1)
    next_a, next_b = d[query + 1], d[nearest + 1]
    near_cos = direction(next_a, next_b)['cosine']
    near_rms = np.sqrt(np.mean((next_a - next_b) ** 2, axis=1))
    # Per-query unconditional historical successors: same causal admissible pool.
    all_cos = 1 - vector_distances(d[1:], d[1:], 'cosine')
    zero = np.linalg.norm(d[1:], axis=1) == 0
    all_cos[zero, :] = 0
    all_cos[:, zero] = 0
    all_rms = cdist(d[1:], d[1:]) / np.sqrt(6)
    base_cos = np.array([all_cos[q, :q - 2].mean() for q in query])
    base_rms = np.array([all_rms[q, :q - 2].mean() for q in query])
    return dict(pair_distance=pair_x, pair_next_cosine=pair_cos, pair_next_distance=pair_next,
                cosine_relation=-correlation(pair_x, pair_cos),
                distance_relation=correlation(pair_x, pair_next),
                nearest_distance=past[np.arange(len(query)), nearest],
                cosine_gain=near_cos - base_cos, distance_gain=base_rms - near_rms,
                nearest_next_cosine=near_cos, nearest_next_distance=near_rms,
                query_indices=query, neighbor_indices=nearest, query_next=next_a,
                neighbor_next=next_b, pair_events=events)


def rolling_distribution(draws, window):
    a = sorted_draws(draws).astype(int)
    if type(window) is not int or not 1 <= window <= len(a):
        raise ValueError('Window outside completed draws')
    x = np.zeros((len(a), 45))
    x[np.arange(len(a))[:, None], a - 1] = 1
    c = np.vstack((np.zeros((1, 45)), np.cumsum(x, axis=0)))
    return (c[window:] - c[:-window]) / (6 * window), np.arange(window, len(a) + 1)


def discrete_w1(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if (a.shape[-1] != 45 or b.shape[-1] != 45 or not np.isfinite(a).all() or
            not np.isfinite(b).all() or np.any(a < 0) or np.any(b < 0) or
            not np.allclose(a.sum(-1), 1) or not np.allclose(b.sum(-1), 1)):
        raise ValueError('Normalized nonnegative probabilities on1..45 required')
    return np.sum(abs(np.cumsum(a - b, axis=-1)[..., :-1]), axis=-1)


def rolling_drift(draws, window, step):
    p, ends = rolling_distribution(draws, window)
    if type(step) is not int or not 1 <= step < len(p):
        raise ValueError('Invalid endpoint step')
    return dict(distance=discrete_w1(p[:-step], p[step:]), endpoints=ends[step:],
                cdf_movement=np.cumsum(p[step:] - p[:-step], axis=1)[:, :-1])


def barycenter(draws, p=2):
    a = sorted_draws(draws)
    if a.ndim != 2 or p not in (1, 2):
        raise ValueError('A collection of draws and p1/2 required')
    return np.mean(a, axis=0) if p == 2 else np.median(a, axis=0)


def barycenter_diagnostic(draws, window, p=1):
    a = sorted_draws(draws)
    if not 1 <= window < len(a):
        raise ValueError('Completed training window plus next draw required')
    c = np.vstack((np.zeros((1, 6)), np.cumsum(a, axis=0)))
    centers = (c[window:-1] - c[:-window - 1]) / window
    next_distance = quantile_distance(centers, a[window:], p)
    unconditional = c[window:-1] / np.arange(window, len(a))[:, None]
    baseline_distance = quantile_distance(unconditional, a[window:], p)
    recent = np.array([quantile_distance(a[i-window:i], centers[i-window], p).mean()
                       for i in range(window, len(a))])
    return dict(barycenters=centers, sorted_mean_baseline=centers.copy(),
                next_distance=next_distance, recent_distance=recent,
                unconditional_distance=baseline_distance, gain=baseline_distance-next_distance,
                movement=quantile_distance(centers[:-1], centers[1:], p),
                target_draws=np.arange(window + 1, len(a) + 1))


def geodesic_residual(draws, p=1):
    a = sorted_draws(draws)
    return quantile_distance(a[1:-1], (a[:-2] + a[2:]) / 2, p)
