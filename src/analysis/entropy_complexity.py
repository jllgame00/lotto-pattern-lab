"""Finite-sample entropy proxies with auditable counts and support masks.

These are plug-in descriptive statistics, not Kolmogorov complexity estimates.
Entropy is in bits except Sample Entropy, which uses natural logarithms.
Support flags do not erase raw finite estimates; callers must respect them
when calibrating or testing a metric against identically processed null data.
"""
import math

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.spatial import cKDTree


def _vector(values, numeric=False):
    values = np.asarray(values)
    if values.ndim != 1 or not values.size:
        raise ValueError('Observations must be a nonempty one-dimensional vector')
    if numeric:
        if values.dtype.kind not in 'biuf':
            raise ValueError('Observations must be real numeric values')
        values = values.astype(float, copy=False)
    if values.dtype.kind in 'biufc' and not np.isfinite(values).all():
        raise ValueError('Observations must be finite')
    return values


def _integer(value, name, choices=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 1:
        raise ValueError(f'{name} must be a positive integer')
    if choices is not None and value not in choices:
        raise ValueError(f'{name} must be one of {choices}')
    return int(value)


def _binary(values):
    values = _vector(values)
    if not np.isin(values, (0, 1)).all():
        raise ValueError('Binary observations must contain only zero and one')
    return values.astype(np.uint8, copy=False)


def _entropy(counts):
    counts = np.asarray(counts)
    positive = counts[counts > 0]
    if not positive.size:
        return 0.
    probabilities = positive / positive.sum()
    return float(-np.sum(probabilities * np.log2(probabilities)))


def shannon(symbols, alphabet=None):
    """Return plug-in symbol entropy and H/log2(theoretical alphabet size).

    ``alphabet`` is a positive size, at least the occupied support. Counts
    follow sorted observed categories, with zero entries for unused categories;
    category labels themselves need not be consecutive integers. When omitted,
    the occupied alphabet is used, with normalized entropy zero for a constant.
    Eligibility requires at least max(10, alphabet) observations; this is a
    support screen, not a claim of negligible plug-in bias.
    """
    values = _vector(symbols)
    try:
        _, counts = np.unique(values, return_counts=True)
    except (TypeError, ValueError) as exc:
        raise ValueError('Symbols must be comparable categories') from exc
    occupied = len(counts)
    alphabet = occupied if alphabet is None else _integer(alphabet, 'alphabet')
    if alphabet < occupied:
        raise ValueError('alphabet cannot be smaller than occupied support')
    counts = np.pad(counts, (0, alphabet - occupied))
    entropy = _entropy(counts)
    return dict(entropy=entropy, normalized=entropy / math.log2(alphabet) if alphabet > 1 else 0.,
                samples=len(values), occupied=occupied, counts=counts,
                eligible=bool(len(values) >= max(10, alphabet)))


def binary_block_entropy(seq, L=1):
    """Entropy of every overlapping L-bit word, with oldest bit most significant.

    H is bits per block; both ``per_symbol`` and ``normalized`` are H/L.
    At least 10 * 2**L overlapping words are required for eligibility.
    """
    values = _binary(seq)
    L = _integer(L, 'L', (1, 2, 3, 4, 5))
    if len(values) < L:
        raise ValueError('Insufficient observations for block length')
    words = sliding_window_view(values, L)
    codes = words @ (1 << np.arange(L - 1, -1, -1))
    counts = np.bincount(codes, minlength=2 ** L)
    entropy = _entropy(counts)
    samples = len(codes)
    return dict(entropy=entropy, per_symbol=entropy / L, normalized=entropy / L,
                samples=samples, occupied=int(np.count_nonzero(counts)), counts=counts,
                eligible=bool(samples >= 10 * 2 ** L))


def conditional_entropy(binary, history=1):
    """Return H(future), H(future|past), and their reduction on N-history rows.

    The joint table has past-context rows (oldest bit most significant) and
    future columns 0/1. Every possible context and both marginal future symbols
    need five observations. All raw entropies remain available if support fails.
    """
    values = _binary(binary)
    history = _integer(history, 'history', (1, 2))
    if len(values) <= history:
        raise ValueError('Insufficient observations for history')
    words = sliding_window_view(values, history + 1)
    contexts = words[:, :history] @ (1 << np.arange(history - 1, -1, -1))
    counts = np.bincount(contexts * 2 + words[:, -1], minlength=2 ** (history + 1)).reshape(-1, 2)
    context_counts = counts.sum(axis=1)
    future_counts = counts.sum(axis=0)
    entropy_future = _entropy(future_counts)
    conditional = max(0., _entropy(counts) - _entropy(context_counts))
    reduction = max(0., entropy_future - conditional)
    return dict(entropy_future=entropy_future, conditional=conditional, reduction=reduction,
                context_counts=context_counts, counts=counts, samples=len(words),
                eligible=bool(np.all(context_counts >= 5) and np.all(future_counts >= 5)))


def permutation_entropy(values, m=3, tau=1):
    """Return ordinal-pattern entropy H/log2(m!) with stable chronological ties.

    ``tie_fraction`` is the fraction of embeddings containing any equal values.
    Eligibility requires at least 5*m! embeddings. This scalar-series statistic
    does not turn binary values into a meaningful ordinal representation;
    callers choose appropriate scalar representations and retain the tie audit.
    Counts use the lexicographic (Lehmer-code) order of index permutations.
    """
    values = _vector(values, numeric=True)
    m = _integer(m, 'm', (3, 4, 5))
    tau = _integer(tau, 'tau', (1, 2, 4, 8))
    span = (m - 1) * tau + 1
    if len(values) < span:
        raise ValueError('Insufficient observations for ordinal embedding')
    embeddings = sliding_window_view(values, span)[:, ::tau]
    patterns = np.argsort(embeddings, axis=1, kind='stable')
    codes = np.zeros(len(patterns), dtype=np.int64)
    for j in range(m - 1):
        smaller = (patterns[:, j + 1:] < patterns[:, j, None]).sum(axis=1)
        codes += smaller * math.factorial(m - j - 1)
    counts = np.bincount(codes, minlength=math.factorial(m))
    ties = np.any(np.diff(np.sort(embeddings, axis=1), axis=1) == 0, axis=1)
    entropy = _entropy(counts)
    samples = len(patterns)
    return dict(entropy=entropy, normalized=entropy / math.log2(math.factorial(m)),
                samples=samples, occupied=int(np.count_nonzero(counts)), counts=counts,
                tie_fraction=float(np.mean(ties)), eligible=bool(samples >= 5 * math.factorial(m)))


def sample_entropy(values, m=2, r=.2):
    """Return -ln(A/B) for common N-m starts and distinct unordered pairs.

    B counts matching m-templates and A matching (m+1)-templates at Chebyshev
    distance <= r*population_std. cKDTree pairs exclude self matches. A>=10,
    B>=20, and positive standard deviation are required for eligibility.
    Zero matches yield None instead of infinity. A constant series has zero
    raw entropy and is explicitly degenerate and ineligible.
    """
    values = _vector(values, numeric=True)
    m = _integer(m, 'm', (2, 3))
    if isinstance(r, (bool, np.bool_)) or not np.isscalar(r):
        raise ValueError('r must be finite and positive')
    try:
        r = float(r)
    except (TypeError, ValueError) as exc:
        raise ValueError('r must be finite and positive') from exc
    if not math.isfinite(r) or r <= 0:
        raise ValueError('r must be finite and positive')
    if len(values) <= m:
        raise ValueError('Insufficient observations for Sample Entropy templates')
    templates = sliding_window_view(values, m + 1)
    std = float(np.std(values, ddof=0))
    radius = r * std
    if std == 0:
        A = B = len(templates) * (len(templates) - 1) // 2
        entropy = 0.
    else:
        B = len(cKDTree(templates[:, :m]).query_pairs(radius, p=np.inf, output_type='ndarray'))
        A = len(cKDTree(templates).query_pairs(radius, p=np.inf, output_type='ndarray'))
        entropy = float(-math.log(A / B)) if A and B else None
    return dict(entropy=entropy, samples=len(templates), A=int(A), B=int(B), std=std,
                radius=radius, degenerate=bool(std == 0), sparse=bool(A < 10 or B < 20),
                eligible=bool(std > 0 and A >= 10 and B >= 20))
