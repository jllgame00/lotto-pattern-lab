"""Generic change-point mathematics on an explicit, finite endpoint grid.

Costs are additive over segments. ``segment`` finds the exact optimum on
the supplied grid, charging a penalty for each interior boundary; it makes
no claim about boundaries outside that grid. Coordinates describe half-open
segments, so boundary ``t`` ends the observations preceding ``t``.
"""

from __future__ import annotations

import numpy as np


def _endpoints(values, *, n=None):
    raw = np.asarray(values)
    if raw.ndim != 1 or raw.size < 2 or raw.dtype.kind not in "iu":
        raise ValueError("endpoints must contain at least two increasing integers")
    if np.any(raw < 0) or np.any(raw[1:] <= raw[:-1]):
        raise ValueError("endpoints must be nonnegative and strictly increasing")
    if n is not None and np.any(raw > n):
        raise ValueError("endpoints must lie within the observation array")
    return raw.astype(np.int64)


def _observations(values, *, binary=False):
    x = np.asarray(values, dtype=float)
    if x.ndim != 2 or min(x.shape) == 0 or not np.isfinite(x).all():
        raise ValueError("observations must be a finite, nonempty N by d array")
    if binary and not np.isin(x, [0, 1]).all():
        raise ValueError("Bernoulli observations must be binary")
    return x


def _minimum(value):
    if isinstance(value, (bool, np.bool_)) or not np.isscalar(value):
        raise ValueError("minimum must be a positive integer")
    if not np.isfinite(value) or value < 1 or value != int(value):
        raise ValueError("minimum must be a positive integer")
    return int(value)


def bernoulli_cost(counts, length):
    """Elementwise minus twice the maximized Bernoulli log likelihood.

    ``counts`` and positive ``length`` broadcast; zero-log-zero terms are
    zero, including a completely absent or completely present dimension.
    """
    k, m = np.broadcast_arrays(np.asarray(counts, dtype=float), np.asarray(length, dtype=float))
    if not np.isfinite(k).all() or not np.isfinite(m).all() or np.any(m <= 0) or np.any(k < 0) or np.any(k > m):
        raise ValueError("counts must be finite and between zero and a positive length")
    p = k / m
    present = np.zeros_like(p)
    absent = np.zeros_like(p)
    np.log(p, out=present, where=k > 0)
    np.log1p(-p, out=absent, where=k < m)
    return -2 * (k * present + (m-k) * absent)


def bernoulli_cost_matrix(x, endpoints, *, per_dimension=False):
    """Compute all forward segment costs using binary prefix counts.

    The optional final axis retains independent dimension costs for batch
    segmentation. Backward and diagonal entries are infinite.
    """
    x = _observations(x, binary=True)
    points = _endpoints(endpoints, n=len(x))
    prefix = np.vstack([np.zeros(x.shape[1]), np.cumsum(x, axis=0)])[points]
    starts, ends = np.triu_indices(len(points), 1)
    costs = np.full((len(points), len(points), x.shape[1]), np.inf)
    costs[starts, ends] = bernoulli_cost(prefix[ends]-prefix[starts], (points[ends]-points[starts])[:, None])
    return costs if per_dimension else costs.sum(axis=2)


def gaussian_cost_matrix(y, endpoints):
    """Aggregate within-segment SSE of already standardized observations.

    Scaling belongs to the caller and must use only its available prefix.
    Centering here improves prefix-square numerical stability without
    changing the segment SSE. Roundoff below zero is clipped to zero.
    """
    y = _observations(y)
    points = _endpoints(endpoints, n=len(y))
    y = y-y[0]
    sums = np.vstack([np.zeros(y.shape[1]), np.cumsum(y, axis=0)])[points]
    squares = np.r_[0., np.cumsum(np.square(y).sum(axis=1))][points]
    starts, ends = np.triu_indices(len(points), 1)
    lengths = points[ends]-points[starts]
    values = squares[ends]-squares[starts]-np.square(sums[ends]-sums[starts]).sum(axis=1)/lengths
    costs = np.full((len(points), len(points)), np.inf)
    costs[starts, ends] = np.maximum(values, 0.)
    return costs


def _cost_input(costs, endpoints, minimum):
    points = _endpoints(endpoints)
    minimum = _minimum(minimum)
    values = np.asarray(costs, dtype=float)
    if values.ndim == 2:
        values = values[:, :, None]
    if values.ndim != 3 or values.shape[:2] != (len(points), len(points)) or values.shape[2] < 1:
        raise ValueError("costs must be M by M or M by M by d for M endpoints")
    forward = values[np.triu_indices(len(points), 1)]
    if not np.isfinite(forward).all():
        raise ValueError("forward segment costs must be finite")
    return values, points, minimum


def segment(costs, endpoints, *, minimum, penalty):
    """Exact finite-grid dynamic programming, batched over the last axis.

    Equal objectives prefer fewer boundaries, then lexicographically earlier
    boundaries. Comparisons do not perturb the floating-point objective.
    Even a two-dimensional cost matrix returns a one-element list.
    """
    values, points, minimum = _cost_input(costs, endpoints, minimum)
    if points[-1]-points[0] < minimum:
        raise ValueError("the whole interval is shorter than minimum")
    if not np.isscalar(penalty) or not np.isfinite(penalty) or penalty < 0:
        raise ValueError("penalty must be finite and nonnegative")
    penalty = float(penalty)
    m, _, d = values.shape
    objective = np.full((m, d), np.inf)
    objective[0] = 0.
    changes = np.full((m, d), m, dtype=int)
    changes[0] = 0
    previous = np.full((m, d), -1, dtype=int)
    paths = [[() for _ in range(d)] for _ in range(m)]
    units = np.arange(d)
    for end in range(1, m):
        starts = np.flatnonzero(points[end]-points[:end] >= minimum)
        if not len(starts):
            continue
        candidates = objective[starts]+values[starts, end]+penalty*(starts[:, None] > 0)
        best = candidates.min(axis=0)
        candidate_changes = changes[starts]+(starts[:, None] > 0)
        tied = candidates == best
        fewest = np.where(tied, candidate_changes, m+1).min(axis=0)
        tied &= candidate_changes == fewest
        chosen = np.argmax(tied, axis=0)
        # Most cells have one minimum. Only exact ties need path comparisons.
        for unit in np.flatnonzero(tied.sum(axis=0) > 1):
            options = np.flatnonzero(tied[:, unit])
            chosen[unit] = min(options, key=lambda row: paths[starts[row]][unit]+((int(points[starts[row]]),) if starts[row] else ()))
        predecessor = starts[chosen]
        reachable = np.isfinite(best)
        objective[end] = best
        changes[end] = fewest
        previous[end, reachable] = predecessor[reachable]
        for unit in units[reachable]:
            start = predecessor[unit]
            paths[end][unit] = paths[start][unit]+((int(points[start]),) if start else ())
    results = []
    for unit in range(d):
        end = m-1
        pieces = []
        raw_cost = 0.
        while end > 0:
            start = int(previous[end, unit])
            pieces.append([int(points[start]), int(points[end])])
            raw_cost += float(values[start, end, unit])
            end = start
        results.append({
            "boundaries": list(paths[-1][unit]), "segments": pieces[::-1],
            "cost": raw_cost, "gain": float(values[0, -1, unit]-raw_cost),
            "objective": float(objective[-1, unit]), "penalty": penalty,
            "minimum": minimum,
        })
    return results


def best_split(costs, endpoints, *, minimum):
    """Best feasible two-segment proposal, independent of any penalty."""
    values, points, minimum = _cost_input(costs, endpoints, minimum)
    eligible = np.flatnonzero((points-points[0] >= minimum) & (points[-1]-points >= minimum))
    results = []
    for unit in range(values.shape[2]):
        whole = float(values[0, -1, unit])
        if not len(eligible):
            results.append({"boundary": None, "gain": 0., "cost": whole})
            continue
        scores = values[0, eligible, unit]+values[eligible, -1, unit]
        choice = int(np.argmin(scores))
        cost = float(scores[choice])
        results.append({"boundary": int(points[eligible[choice]]), "gain": whole-cost, "cost": cost})
    return results


def cusum(x, *, minimum=26):
    """Prefix-centered CUSUM divided by sqrt(N) and population deviation.

    Maxima use only splits with two segments of at least ``minimum`` rows.
    Constant columns (including variation within eight relative machine
    epsilons) and unavailable splits have score zero and location -1. The
    curve includes both the zero and final endpoints.
    """
    x = _observations(x)
    minimum = _minimum(minimum)
    n, d = x.shape
    # Subtract an observed reference before taking the mean: summing a
    # repeated non-integer value can otherwise invent a nonzero deviation.
    shifted = x-x[0]
    centered = shifted-shifted.mean(axis=0)
    scale = np.sqrt(n)*centered.std(axis=0, ddof=0)
    tolerance = 8*np.finfo(float).eps*np.max(np.abs(x), axis=0)
    varying = (np.ptp(x, axis=0) > tolerance) & (scale > 0)
    curve = np.vstack([np.zeros(d), np.cumsum(centered, axis=0)])
    np.divide(curve, scale, out=curve, where=varying)
    curve[:, ~varying] = 0.
    score = np.zeros(d)
    location = np.full(d, -1, dtype=int)
    if n >= 2*minimum:
        eligible = np.abs(curve[minimum:n-minimum+1])
        maximum = np.argmax(eligible, axis=0)
        score = eligible[maximum, np.arange(d)]
        location[varying] = (maximum+minimum)[varying]
    return {"score": score, "location": location, "curve": curve}


def distribution_distance(a, b):
    """Raw rate L1/max shift, normalized Jensen-Shannon divergence in nats,
    and cosine similarity for finite nonnegative positive-mass vectors.
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.ndim != 1 or b.shape != a.shape or not a.size or not np.isfinite(a).all() or not np.isfinite(b).all() or np.any(a < 0) or np.any(b < 0) or a.max() <= 0 or b.max() <= 0:
        raise ValueError("vectors must have equal shape, finite nonnegative values and positive mass")
    # Rescale before summing so finite inputs need not have finite raw mass.
    p, q = a/a.max(), b/b.max()
    p, q = p/p.sum(), q/q.sum()
    middle = (p+q)/2
    js = 0.
    for distribution in (p, q):
        positive = distribution > 0
        js += .5*float(np.sum(distribution[positive]*np.log(distribution[positive]/middle[positive])))
    difference = np.abs(a-b)
    return {"l1": float(difference.sum()), "js": js,
            "cosine": float(np.dot(p, q)/(np.linalg.norm(p)*np.linalg.norm(q))),
            "max_shift": float(difference.max())}


def boundary_concordance(a, b, *, tolerance):
    """One-to-one maximum-cardinality sorted boundary matching and F1.

    The greedy match is optimal for ordered points with a fixed distance
    tolerance. Empty boundary sets do not provide evidence of concordance.
    """
    if not np.isscalar(tolerance) or not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    left, right = np.asarray(a), np.asarray(b)
    if left.ndim != 1 or right.ndim != 1 or not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("boundaries must be finite one-dimensional arrays")
    left, right = np.sort(left), np.sort(right)
    i = j = matches = 0
    while i < len(left) and j < len(right):
        if abs(left[i]-right[j]) <= tolerance:
            matches += 1
            i += 1
            j += 1
        elif left[i] < right[j]:
            i += 1
        else:
            j += 1
    count = len(left)+len(right)
    return {"f1": 2*matches/count if count else 0., "matches": matches,
            "count_a": len(left), "count_b": len(right)}
