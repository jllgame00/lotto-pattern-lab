"""Phase 15 absolute-distance and gap-shape geometry on six-of-45 draws.

Draw endpoints and reported neighbor draws are one-based. Distance zero is
retained as a reference in temporal tables; inferential callers use 1..44.
"""
from math import comb
from numbers import Integral

import numpy as np
from scipy.spatial.distance import cdist

from .recurrence import research_matrix


LAGS = (1, 2, 3, 4, 8, 13, 26)
_PAIR_I, _PAIR_J = np.triu_indices(6, 1)
_DISTANCES = np.arange(1, 45)
_PAIR_EXPECTED = (45 - _DISTANCES) / 66
_ADJACENT_EXPECTED = np.array([5 * comb(45 - int(d), 5) / comb(45, 6)
                               for d in _DISTANCES])


def _integer(value):
    return isinstance(value, Integral) and not isinstance(value, (bool, np.bool_))


def representation(x, cutoff=None):
    """Return nonwrapping pair/gap arrays and exact IID per-draw expectations.

    ``cutoff`` certifies the supplied prefix; it never silently truncates.
    Histograms and expectations have columns for distances 1 through 44.
    """
    x = research_matrix(x)
    if cutoff is not None and (not _integer(cutoff) or cutoff != len(x)):
        raise ValueError('Cutoff must exactly match the supplied research prefix')
    numbers = (np.nonzero(x)[1] + 1).reshape(-1, 6)
    gaps = np.diff(numbers, axis=1)
    pairs = numbers[:, _PAIR_J] - numbers[:, _PAIR_I]
    normalized = gaps / (numbers[:, -1] - numbers[:, 0])[:, None]
    offsets = np.arange(len(x))[:, None] * 44
    pair_hist = np.bincount((pairs - 1 + offsets).ravel(), minlength=len(x) * 44).reshape(-1, 44)
    adjacent_hist = np.bincount((gaps - 1 + offsets).ravel(), minlength=len(x) * 44).reshape(-1, 44)
    return dict(sorted_numbers=numbers, gaps=gaps, pairwise=pairs,
                anchored=numbers - numbers[:, :1], normalized_gaps=normalized,
                gap_entropy=-(normalized * np.log2(normalized)).sum(axis=1),
                pair_histogram=pair_hist, adjacent_histogram=adjacent_hist,
                pair_expected=_PAIR_EXPECTED.copy(), adjacent_expected=_ADJACENT_EXPECTED.copy(),
                opportunities=45 - _DISTANCES)


def absolute_relation(x, lag):
    """All temporal absolute-distance counts, opportunities and conditional z.

    For each row and distance, a target's weight is the number of source
    numbers at that distance. Variance is exact for six targets sampled
    without replacement, conditional on the observed source rows. ``support``
    is the observed pair count; ``source_counts`` is the 45 source marginals.
    These z values are diagnostics, not normal-theory p values.
    """
    x = research_matrix(x)
    if not _integer(lag) or lag not in LAGS or lag >= len(x):
        raise ValueError('Lag must be predeclared and leave at least one aligned row')
    source, future = x[:-lag], x[lag:]
    cross = source.astype(float).T @ future.astype(float)
    observed = np.empty(45, dtype=np.int64)
    opportunity = np.empty(45, dtype=np.int64)
    variance = np.empty(45, dtype=float)
    for d in range(45):
        if d == 0:
            weights = source.astype(np.uint8)
            observed[d] = np.trace(cross)
        else:
            weights = np.zeros(source.shape, dtype=np.uint8)
            weights[:, d:] = source[:, :-d]
            weights[:, :-d] += source[:, d:]
            observed[d] = np.trace(cross, offset=d) + np.trace(cross, offset=-d)
        total = weights.sum(axis=1).astype(float)
        opportunity[d] = total.sum()
        second = np.square(weights).sum(axis=1) / 45
        variance[d] = (6 * 39 / 44) * np.sum(second - np.square(total / 45))
    variance = np.maximum(variance, 0)
    expected = (6 / 45) * opportunity
    z = np.divide(observed - expected, np.sqrt(variance),
                  out=np.zeros(45), where=variance > 0)
    return dict(observed=observed, opportunity=opportunity, expected=expected,
                variance=variance, var=variance, z=z,
                source_counts=source.sum(axis=0), support=observed.copy())


def shape_distance(a, b):
    """Euclidean distance for five normalized gaps, or a pairwise distance matrix.

    Two vectors produce a float; either matrix input produces a 2D matrix.
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    scalar = a.ndim == b.ndim == 1
    if (a.ndim not in (1, 2) or b.ndim not in (1, 2)
            or a.shape[-1] != 5 or b.shape[-1] != 5
            or not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError('Shape coordinates must be finite vectors or matrices of five gaps')
    result = cdist(np.atleast_2d(a), np.atleast_2d(b), metric='euclidean')
    return float(result[0, 0]) if scalar else result


def shape_successor(x, K, endpoints=None):
    """Causal nearest-shape successor MSE against all eligible successors.

    At one-based endpoint ``end``, query index is ``end-1``, candidate index
    ``j <= query-26``, and successor ``j+1 < query``. Ties choose earlier draws.
    The default query grid is 104, 130, ... plus the last observable endpoint
    ``len(x)-1``. No target beyond the supplied research prefix is accessed.
    """
    shapes = representation(x)['normalized_gaps']
    if not _integer(K) or K not in (10, 25):
        raise ValueError('K must be one of the predeclared values 10 and 25')
    if endpoints is None:
        ends = sorted(set(range(104, len(shapes), 26)) | {len(shapes) - 1})
        ends = [end for end in ends if end - 26 >= K]
    else:
        ends = list(endpoints)
        if (len(set(ends)) != len(ends)
                or any(not _integer(end) or not K + 26 <= end < len(shapes) for end in ends)):
            raise ValueError('Endpoints need K eligible neighbors and an observed next draw')
    rows, predictions, baseline_predictions, actual = [], [], [], []
    for end in ends:
        query = end - 1
        candidates = np.arange(query - 26 + 1)
        distances = shape_distance(shapes[query], shapes[candidates])[0]
        neighbors = np.argsort(distances, kind='stable')[:K]
        successors = shapes[candidates + 1]
        anchor = successors[0]
        # Center before averaging so identical shapes have exact zero MSE.
        prediction = anchor + (successors[neighbors] - anchor).mean(axis=0)
        baseline = anchor + (successors - anchor).mean(axis=0)
        truth = shapes[end]
        mse_model = float(np.mean(np.square(prediction - truth)))
        mse_baseline = float(np.mean(np.square(baseline - truth)))
        rows.append(dict(endpoint=int(end), target_draw=int(end + 1), K=int(K),
                         neighbor_draws=(candidates[neighbors] + 1).tolist(),
                         nearest_distance=float(distances[neighbors].mean()),
                         baseline_distance=float(distances.mean()),
                         mse_model=mse_model, mse_baseline=mse_baseline,
                         gain=mse_baseline - mse_model))
        predictions.append(prediction)
        baseline_predictions.append(baseline)
        actual.append(truth)
    gains = np.array([row['gain'] for row in rows])
    se = float(gains.std(ddof=1) / np.sqrt(len(gains))) if len(gains) > 1 else 0.
    score = float(gains.mean() / se) if se > 0 else 0.
    return dict(score=score, rows=rows, gains=gains,
                predictions=np.array(predictions).reshape(-1, 5),
                baseline_predictions=np.array(baseline_predictions).reshape(-1, 5),
                actual=np.array(actual).reshape(-1, 5))
