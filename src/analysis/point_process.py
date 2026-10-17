"""Causal discrete event summaries for Phase 20's fixed research scope.

Draw indices in event lists are one-based. Predictor states at row t use only
rows preceding t; recent counts instead describe completed draws ending at t.
Lag matrices use source on axis zero and target on axis one. These summaries
are descriptive pseudo-likelihood statistics; they do not assume 45 independent
processes and require the complete-search null for inferential use.
"""
from numbers import Integral, Real

import numpy as np

from src.analysis.recurrence import research_matrix

LAGS = (1, 2, 3, 4, 8, 13, 26)
SCHEMES = ('clipped', 'coarse', 'relative')
STATE_COUNTS = {'clipped': 27, 'coarse': 6, 'relative': 5}
KERNELS = ('exp2', 'exp8', 'finite')
P = 6 / 45


def _parameters(alpha, minimum):
    if (isinstance(alpha, (bool, np.bool_)) or not isinstance(alpha, Real)
            or not np.isfinite(alpha) or alpha <= 0):
        raise ValueError('alpha must be finite and positive')
    if (isinstance(minimum, (bool, np.bool_)) or not isinstance(minimum, Integral)
            or minimum <= 0):
        raise ValueError('minimum must be a positive integer')


def _scheme(scheme):
    if not isinstance(scheme, str) or scheme not in SCHEMES:
        raise ValueError('Unknown renewal representation')


def event_history(x):
    """Return fresh event/interarrival arrays and strictly prior event states.

    gaps is (N,45), with -1 before an own event is observed. A prior event
    at t-1 gives gap 0. Relative gaps divide this gap by the mean completed
    own interarrival, requiring two prior own events. current_* describe the
    next target after all N observed draws. recent_counts[w][t] counts the
    available completed draws max(0,t-w+1)..t, including draw t itself; it is
    therefore NOT a predictor for that same target row.
    """
    x = research_matrix(x)
    n = len(x)
    targets = np.arange(1, n + 2)
    gaps = np.full((n + 1, 45), -1, dtype=int)
    relative = np.full((n + 1, 45), np.nan)
    events, interarrivals = [], []
    for j in range(45):
        event = np.flatnonzero(x[:, j]) + 1
        events.append(event)
        interarrivals.append(np.diff(event))
        prior = np.searchsorted(event, targets, side='left')
        seen = prior > 0
        gaps[seen, j] = targets[seen] - event[prior[seen] - 1] - 1
        completed = prior >= 2
        if completed.any():
            mean = (event[prior[completed] - 1] - event[0]) / (prior[completed] - 1)
            relative[completed, j] = gaps[completed, j] / mean
    cumulative = np.vstack((np.zeros((1, 45), dtype=int), np.cumsum(x, axis=0)))
    ends = np.arange(1, n + 1)
    recent = {w: cumulative[ends] - cumulative[np.maximum(0, ends - w)]
              for w in (10, 26, 52)}
    return {'events': events, 'interarrivals': interarrivals,
            'gaps': gaps[:-1], 'relative': relative[:-1],
            'current_gap': gaps[-1], 'current_relative': relative[-1],
            'recent_counts': recent}


def _states(history, scheme, current=False):
    _scheme(scheme)
    prefix = 'current_' if current else ''
    gap = history[prefix + 'gap' if current else 'gaps']
    if scheme == 'relative':
        value = history[prefix + 'relative']
        return np.where(np.isfinite(value),
                        np.searchsorted([.5, 1, 2, 3], value, side='right'), -1)
    if scheme == 'clipped':
        return np.minimum(gap, 26)
    return np.where(gap >= 0, np.searchsorted([1, 3, 7, 13, 26], gap, side='right'), -1)


def renewal_states(x, scheme):
    """Return (N,45) pre-target states, -1 for left-censored states."""
    _scheme(scheme)
    return _states(event_history(x), scheme)


def current_renewal_state(x, scheme):
    """Return 45 renewal states for the next target after observed history."""
    _scheme(scheme)
    return _states(event_history(x), scheme, current=True)


def renewal_table(x, scheme, alpha=26, minimum=20):
    """Counts and smoothed hazards by number/state, all (45,S).

    baseline alone has shape (45,): (eligible own wins+2)/(eligible rows+15).
    Here eligible own rows means uncensored states, before the support filter.
    Unsupported hazards equal that baseline; raw rates are NaN. score is the
    absolute standardized effect; eligible marks finite cells meeting minimum.
    """
    _parameters(alpha, minimum)
    _scheme(scheme)
    x = research_matrix(x)
    states = renewal_states(x, scheme)
    size = STATE_COUNTS[scheme]
    valid = states >= 0
    codes = states + np.arange(45)[None, :] * size
    support = np.bincount(codes[valid], minlength=45 * size).reshape(45, size)
    hits = np.bincount(codes[valid & x], minlength=45 * size).reshape(45, size)
    baseline = (hits.sum(axis=1) + 2) / (support.sum(axis=1) + 15)
    b = baseline[:, None]
    conditional = (hits + alpha * b) / (support + alpha)
    effect = conditional - b
    rate = np.divide(hits, support, out=np.full(support.shape, np.nan), where=support > 0)
    score = np.abs(effect) * np.sqrt(support / (b * (1 - b)))
    return {'support': support, 'hits': hits, 'rate': rate, 'baseline': baseline,
            'conditional': conditional, 'effect': effect, 'score': score,
            'eligible': (support >= minimum) & np.isfinite(score)}


def lag_effects(x, lag, alpha=26, minimum=30):
    """Signed effects of source_i(t-lag) on target_j(t), arrays (45,45).

    baseline is broadcast over sources from (aligned target wins+2)/(n+15).
    Empty alignments are allowed and return the prior baseline with no support.
    Raw unsupported rates are NaN; conditional/lift/score are neutral there.
    """
    _parameters(alpha, minimum)
    if (isinstance(lag, (bool, np.bool_)) or not isinstance(lag, Integral)
            or lag not in LAGS):
        raise ValueError('lag must be an integer in the predeclared LAGS')
    x = research_matrix(x)
    return _lag_effects(x, lag, alpha, minimum)


def _lag_effects(x, lag, alpha, minimum):
    n = max(0, len(x) - lag)
    source = x[:n].astype(float)
    target = x[lag:]
    hits = (source.T @ target.astype(float)).astype(np.int64)
    support = np.broadcast_to(source.sum(axis=0).astype(np.int64)[:, None], (45, 45)).copy()
    baseline = np.broadcast_to((target.sum(axis=0) + 2) / (n + 15), (45, 45)).copy()
    conditional = (hits + alpha * baseline) / (support + alpha)
    effect = conditional - baseline
    rate = np.divide(hits, support, out=np.full((45, 45), np.nan), where=support > 0)
    score = effect * np.sqrt(support / (baseline * (1 - baseline)))
    log_odds = (np.log(conditional) - np.log1p(-conditional)
                - np.log(baseline) + np.log1p(-baseline))
    return {'n': n, 'support': support, 'hits': hits, 'baseline': baseline,
            'rate': rate, 'conditional': conditional, 'lift': conditional / baseline,
            'log_odds': log_odds, 'effect': effect, 'score': score,
            'eligible': (support >= minimum) & np.isfinite(score)}


def all_effects(x, alpha=26, minimum=30):
    """Stack lag_effects arrays in fixed LAGS order, shape (7,45,45)."""
    _parameters(alpha, minimum)
    x = research_matrix(x)
    results = [_lag_effects(x, lag, alpha, minimum) for lag in LAGS]
    out = {key: np.stack([row[key] for row in results]) for key in results[0]}
    out['lags'] = LAGS
    return out


def kernel_effects(x, alpha=26, minimum=30, effects=None):
    """Return (3,45,45) kernel score/amplitude/eligibility arrays.

    exp2/exp8 project residual counts on exp(-(lag-1)/tau), normalized by
    summed diagonal count variance; score is the squared projection z.
    Amplitude is the least squares effect projection sum(w*effect)/sum(w²).
    finite uses mean squared signed lag score and RMS effect. All seven lag
    cells must be eligible. Cells with missing lag support have NaN scores.
    Optional effects is an all_effects result for the same x/parameters; callers
    supplying it are responsible for provenance and parameter correspondence.
    """
    _parameters(alpha, minimum)
    x = research_matrix(x)
    if effects is None:
        effects = all_effects(x, alpha, minimum)
    values = {}
    for key in ('support', 'baseline', 'effect', 'score', 'eligible'):
        if key not in effects or np.shape(effects[key]) != (7, 45, 45):
            raise ValueError('effects must contain arrays shaped (7,45,45)')
        values[key] = np.asarray(effects[key])
    support, baseline, effect = (values[k] for k in ('support', 'baseline', 'effect'))
    supported = ((support > 0) & np.isfinite(effect) & np.isfinite(baseline)
                 & (baseline > 0) & (baseline < 1)).all(axis=0)
    eligible = values['eligible'].astype(bool).all(axis=0) & supported
    variance = support * baseline * (1 - baseline)
    residual = effect * support
    scores, amplitudes = [], []
    for tau in (2, 8):
        weights = np.exp(-(np.asarray(LAGS) - 1) / tau)[:, None, None]
        numerator = np.sum(weights * residual, axis=0)
        denominator = np.sum(weights * weights * variance, axis=0)
        score = np.divide(numerator * numerator, denominator,
                          out=np.full((45, 45), np.nan), where=denominator > 0)
        scores.append(np.where(supported, score, np.nan))
        amplitudes.append(np.where(supported, np.sum(weights * effect, axis=0)
                                  / np.sum(weights * weights), np.nan))
    scores.append(np.where(supported, np.mean(values['score'] ** 2, axis=0), np.nan))
    amplitudes.append(np.where(supported, np.sqrt(np.mean(effect ** 2, axis=0)), np.nan))
    return {'names': KERNELS, 'score': np.stack(scores), 'amplitude': np.stack(amplitudes),
            'eligible': np.broadcast_to(eligible, (3, 45, 45)).copy()}
