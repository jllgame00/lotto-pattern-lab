"""Auditable discrete information in bits, without a six-of-45 assumption.

Pair matrices use source variable i on axis 0 and target j on axis 1,
including the diagonal. Counts retain every possible binary state, including
zeros. ``raw`` is the plug-in estimate. ``corrected`` uses Miller--Madow
entropy corrections with occupied states and deliberately retains negatives.
Eligibility and sparse-table diagnostics are separate from these estimates.
"""
import numpy as np


LAGS = (1, 2, 3, 4, 8, 13, 26)
HISTORIES = ((1, 1), (1, 2), (2, 1), (2, 2))


def _categorical_codes(values):
    values = np.asarray(values)
    if values.ndim != 1 or not len(values):
        raise ValueError('Discrete observations must be nonempty one-dimensional arrays')
    if values.dtype.kind in 'biufc' and not np.isfinite(values).all():
        raise ValueError('Discrete observations must be finite')
    try:
        _, codes = np.unique(values, return_inverse=True)
    except (TypeError, ValueError) as exc:
        raise ValueError('Discrete observations must have comparable categories') from exc
    return codes


def _entropy(counts, axes):
    """Plug-in entropy and occupied support size over the supplied state axes."""
    counts = np.asarray(counts)
    total = counts.sum(axis=axes, keepdims=True)
    p = np.divide(counts, total, out=np.zeros(counts.shape, dtype=float), where=total > 0)
    logs = np.zeros_like(p)
    np.log2(p, out=logs, where=p > 0)
    return -(p * logs).sum(axis=axes), (counts > 0).sum(axis=axes)


def discrete_mi(x, y):
    """Return the raw discrete mutual information I(X;Y), as a float in bits.

    Categories may be numeric or strings; no continuity or binary assumption
    is imposed. Empty, nonfinite, or unequally sized observations are errors.
    """
    a, b = _categorical_codes(x), _categorical_codes(y)
    if len(a) != len(b):
        raise ValueError('Discrete observations must have equal lengths')
    n_b = int(b.max()) + 1
    counts = np.bincount(a * n_b + b, minlength=(int(a.max()) + 1) * n_b).reshape(-1, n_b)
    h_a, _ = _entropy(counts.sum(1), -1)
    h_b, _ = _entropy(counts.sum(0), -1)
    h_ab, _ = _entropy(counts, (0, 1))
    return float(max(0., h_a + h_b - h_ab))


def conditional_mi(x, y, z):
    """Return raw I(X;Y|Z) in bits for equally sized categorical sequences."""
    a, b, c = (_categorical_codes(v) for v in (x, y, z))
    if len(a) != len(b) or len(a) != len(c):
        raise ValueError('Discrete observations must have equal lengths')
    n_a, n_b, n_c = (int(v.max()) + 1 for v in (a, b, c))
    counts = np.bincount((a * n_c + c) * n_b + b, minlength=n_a * n_c * n_b).reshape(n_a, n_c, n_b)
    h_ac, _ = _entropy(counts.sum(2), (0, 1))
    h_bc, _ = _entropy(counts.sum(0), (0, 1))
    h_c, _ = _entropy(counts.sum((0, 2)), -1)
    h_abc, _ = _entropy(counts, (0, 1, 2))
    return float(max(0., h_ac + h_bc - h_c - h_abc))


def _binary_matrix(x):
    x = np.asarray(x)
    if x.ndim != 2 or min(x.shape) < 1 or not np.isin(x, (0, 1)).all():
        raise ValueError('Expected a nonempty time-by-variable binary matrix')
    return x.astype(np.uint8, copy=False)


def _integer(value, name, minimum=1):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')


def lagged_states(x, lag, k, l, source=None):
    """Build nonwrapping source, target past, and target future state codes.

    At time t, source=sum(2**r * source[t-lag-r], r=0..l-1),
    past=sum(2**r * x[t-1-r], r=0..k-1), and future=x[t].
    The first valid time is ``start=max(lag+l-1,k)``. Replacement source
    changes only source histories; target history and future always use x.
    """
    _integer(lag, 'lag')
    _integer(k, 'k')
    _integer(l, 'l')
    if k not in (1, 2) or l not in (1, 2):
        raise ValueError('History lengths k and l must be 1 or 2')
    x = _binary_matrix(x)
    source = x if source is None else _binary_matrix(source)
    if source.shape != x.shape:
        raise ValueError('Replacement source must have the same shape as target')
    start = max(lag + l - 1, k)
    if start >= len(x):
        raise ValueError('Insufficient observations for requested history')
    end = len(x)
    s = sum((2 ** r) * source[start - lag - r:end - lag - r] for r in range(l))
    z = sum((2 ** r) * x[start - 1 - r:end - 1 - r] for r in range(k))
    return dict(source=s, past=z, future=x[start:], start=start)


def _pair_counts(source, target, n_source, n_target):
    """All variable-pair tables with one float64 one-hot matrix product."""
    n, m = source.shape
    left = (source[:, :, None] == np.arange(n_source)).reshape(n, m * n_source).astype(float)
    right = (target[:, :, None] == np.arange(n_target)).reshape(n, m * n_target).astype(float)
    table = np.rint(left.T @ right).astype(np.int64)
    return table.reshape(m, n_source, m, n_target).transpose(0, 2, 1, 3)


def _thresholds(min_samples, min_count, min_events):
    _integer(min_samples, 'min_samples')
    _integer(min_count, 'min_count', 0)
    _integer(min_events, 'min_events', 0)


def _diagnostics(counts, axes):
    occupied = (counts > 0).sum(axis=axes)
    possible = np.prod([counts.shape[axis] for axis in axes])
    sparse = ((counts > 0) & (counts < 5)).any(axis=axes) | (occupied / possible < .8)
    return occupied, sparse


def mi_matrix(x, lag, source=None, min_samples=300, min_count=8, min_events=20):
    """Return all I(source_i[t-lag]; target_j[t]) tables and estimates.

    ``counts`` is (m,m,2,2); ``source_counts`` and ``future_counts``
    are (m,2). Eligibility requires N>=min_samples and both states in
    each marginal >=min_events. min_count is accepted for a common MI/TE
    interface and has no role in unconditional MI eligibility.
    ``sparse`` flags any occupied joint cell <5 or occupied fraction <.8.
    """
    _thresholds(min_samples, min_count, min_events)
    state = lagged_states(x, lag, 1, 1, source=source)
    counts = _pair_counts(state['source'], state['future'], 2, 2)
    n = len(state['future'])
    source_counts = counts[:, 0].sum(2)
    future_counts = counts[0].sum(1)
    hs, os = _entropy(source_counts, -1)
    hy, oy = _entropy(future_counts, -1)
    hsy, occupied = _entropy(counts, (2, 3))
    raw = np.maximum(0., hs[:, None] + hy[None, :] - hsy)
    correction = (os[:, None] + oy[None, :] - occupied - 1) / (2 * n * np.log(2))
    _, sparse = _diagnostics(counts, (2, 3))
    eligible = ((n >= min_samples) & (source_counts.min(1)[:, None] >= min_events)
                & (future_counts.min(1)[None, :] >= min_events))
    return dict(counts=counts, raw=raw, corrected=raw + correction,
                samples=n, occupied=occupied, sparse=sparse, eligible=eligible,
                source_counts=source_counts, future_counts=future_counts)


def te_matrix(x, lag, k, l, source=None, min_samples=300, min_count=8, min_events=20):
    """Return I(source history_i; future_j | target history_j), in bits.

    ``counts`` is (m,m,2**l,2**k,2), ordered source, target, source
    history, target past, future. Marginal arrays: source_counts(m,2**l),
    past_counts(m,2**k), future_counts(m,2), source_past_counts(m,m,2**l,2**k),
    and past_future_counts(m,2**k,2). Eligibility requires N>=min_samples,
    both future states >=min_events, and EVERY possible source and target
    history marginal state >=min_count. Sparse diagnostics do not remove
    states or change eligibility. All arrays retain ineligible estimates.
    """
    _thresholds(min_samples, min_count, min_events)
    state = lagged_states(x, lag, k, l, source=source)
    n = len(state['future'])
    counts = _pair_counts(state['source'], state['past'] * 2 + state['future'], 2 ** l, 2 ** (k + 1))
    counts = counts.reshape(*counts.shape[:3], 2 ** k, 2)
    source_past = counts.sum(4)
    past_future = counts[0].sum(1)
    source_counts = counts[:, 0].sum((2, 3))
    past_counts = past_future.sum(2)
    future_counts = past_future.sum(1)
    hsz, osz = _entropy(source_past, (2, 3))
    hzy, ozy = _entropy(past_future, (1, 2))
    hz, oz = _entropy(past_counts, -1)
    hszy, occupied = _entropy(counts, (2, 3, 4))
    raw = np.maximum(0., hsz + hzy[None, :] - hz[None, :] - hszy)
    correction = (osz + ozy[None, :] - oz[None, :] - occupied) / (2 * n * np.log(2))
    _, sparse = _diagnostics(counts, (2, 3, 4))
    eligible = ((n >= min_samples) & (source_counts.min(1)[:, None] >= min_count)
                & (past_counts.min(1)[None, :] >= min_count)
                & (future_counts.min(1)[None, :] >= min_events))
    return dict(counts=counts, raw=raw, corrected=raw + correction,
                samples=n, occupied=occupied, sparse=sparse, eligible=eligible,
                source_counts=source_counts, past_counts=past_counts,
                future_counts=future_counts, source_past_counts=source_past,
                past_future_counts=past_future)
