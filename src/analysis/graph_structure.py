"""Causal six-of-45 co-occurrence graphs and frequency-adjusted diagnostics.

Draw endpoints are one-based. Callers must supply the exact history prefix:
``cutoff`` is an assertion of its length, never an instruction to truncate.
No graph quantity implies predictive evidence; strength is identically 5*f.
"""
import numpy as np

from src.analysis.recurrence import research_matrix


WINDOWS = (26, 52, 104)
_UPPER = np.triu_indices(45, 1)


def _positive_integer(value, name):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 1:
        raise ValueError(f'{name} must be a positive integer')


def _vector(values, name):
    result = np.asarray(values, dtype=float)
    if result.shape != (45,) or not np.isfinite(result).all():
        raise ValueError(f'{name} must contain 45 finite node values')
    return result


def _adjacency(values):
    if isinstance(values, dict):
        values = values['adjacency']
    a = np.asarray(values, dtype=float)
    if (a.shape != (45, 45) or not np.isfinite(a).all() or np.any(a < 0)
            or not np.allclose(a, a.T) or np.any(a.diagonal() != 0)):
        raise ValueError('A finite nonnegative symmetric zero-diagonal 45x45 adjacency is required')
    return a


def freq_edge_expectation(frequency, window):
    """Fixed frequency-conditioned reference (45/44)*(5/6)*f_i*f_j/W.

    This reference is an explicitly approximate marginal correction, not an
    exact conditional randomization model. Its diagonal is always zero.
    """
    f = _vector(frequency, 'frequency')
    _positive_integer(window, 'window')
    if np.any(f < 0) or np.any(f > window):
        raise ValueError('Frequencies must be within the graph window')
    expected = (45 / 44) * (5 / 6) * np.outer(f, f) / window
    np.fill_diagonal(expected, 0)
    return expected


def graph(x, window=None, cutoff=None, threshold=2):
    """Build weighted and thresholded undirected graphs on all 45 numbers.

    ``window=None`` uses the complete prefix. Each draw adds its 15 unordered
    pairs once. Binary motifs use A>=threshold and count all 45 nodes; local
    clustering is zero below degree two. ``common_neighbors=B@B`` retains
    diagonal=degree. Concentration uses unordered weights and denominator
    (15W)^2. Expectations assume independent uniform six-of-45 draws.
    """
    x = research_matrix(x)
    if cutoff is not None:
        _positive_integer(cutoff, 'cutoff')
        if cutoff != len(x):
            raise ValueError('cutoff must equal the exact supplied prefix length')
    _positive_integer(threshold, 'threshold')
    if window is None:
        window = len(x)
    _positive_integer(window, 'window')
    if window > len(x):
        raise ValueError('window exceeds supplied history')
    recent = x[-window:].astype(np.int64)
    f = recent.sum(axis=0)
    a = recent.T @ recent
    np.fill_diagonal(a, 0)
    strength = a.sum(axis=1)
    if not np.array_equal(strength, 5 * f):
        raise AssertionError('Six-of-45 graph strength must equal five times frequency')
    binary = a >= threshold
    b = binary.astype(np.int64)
    degree = b.sum(axis=1)
    common = b @ b
    # diag(B^3) counts each triangle incident on the node twice.
    triangle_incidence = (common * b).sum(axis=1)
    triangles = int(triangle_incidence.sum() // 6)
    local_wedges = degree * (degree - 1) // 2
    wedges = int(local_wedges.sum())
    clustering = np.divide(triangle_incidence, 2 * local_wedges,
                           out=np.zeros(45), where=local_wedges > 0)
    expected = freq_edge_expectation(f, window)
    return dict(adjacency=a, binary=binary, frequency=f, strength=strength,
                degree=degree, density=float(b.sum() / (45 * 44)),
                local_clustering=clustering, clustering=float(clustering.mean()),
                triangles=triangles, wedges=wedges,
                transitivity=3 * triangles / wedges if wedges else 0.,
                common_neighbors=common,
                concentration=float(np.square(a[_UPPER]).sum() / (15 * window) ** 2),
                expected_pair=window / 66, node_expected_strength=2 * window / 3,
                expected_concentration=1 / 990 + (1 - 1 / 66) / (15 * window),
                frequency_expectation=expected, residual_adjacency=a - expected,
                window=int(window), cutoff=len(x), threshold=int(threshold))


def residualize(values, frequency):
    """OLS node residuals against an intercept and frequency, even if constant."""
    values, f = _vector(values, 'values'), _vector(frequency, 'frequency')
    # Centering f improves conditioning without changing the OLS subspace.
    design = np.column_stack((np.ones(45), f - f.mean()))
    coefficient = np.linalg.lstsq(design, values, rcond=None)[0]
    return values - design @ coefficient


def standardize(values):
    """Center and scale with population SD; numerical constants become zero."""
    values = _vector(values, 'values')
    scale = values.std()
    return (values - values.mean()) / scale if scale > 1e-12 else np.zeros(45)


def similarity(a, b, threshold=2):
    """Upper-edge cosine/Pearson/Jaccard and full-matrix Frobenius distance.

    Two zero vectors have similarity one; a zero and nonzero vector have
    cosine/Pearson zero. Two identical constant edge vectors have Pearson
    one, and other zero-variance Pearson comparisons return zero. Empty
    thresholded edge unions have Jaccard one.
    """
    _positive_integer(threshold, 'threshold')
    a, b = _adjacency(a), _adjacency(b)
    left, right = a[_UPPER], b[_UPPER]

    def cosine(u, v):
        nu, nv = np.linalg.norm(u), np.linalg.norm(v)
        if nu == 0 or nv == 0:
            return float(nu == nv)
        return float(np.clip(u @ v / (nu * nv), -1, 1))

    centered_left, centered_right = left - left.mean(), right - right.mean()
    if np.linalg.norm(centered_left) == 0 or np.linalg.norm(centered_right) == 0:
        correlation = float(np.array_equal(left, right))
    else:
        correlation = cosine(centered_left, centered_right)
    binary_left, binary_right = left >= threshold, right >= threshold
    union = np.count_nonzero(binary_left | binary_right)
    return dict(cosine=cosine(left, right), correlation=correlation,
                frobenius=float(np.linalg.norm(a - b)),
                jaccard=float(np.count_nonzero(binary_left & binary_right) / union) if union else 1.)


graph_similarity = similarity


def spectral_partition(adjacency, communities=2):
    """Deterministic normalized-adjacency spectral partition with isolates -1.

    Use the largest algebraic eigenvectors, row-normalization, first active
    node then farthest-point initialization (ties choose the lowest node),
    and at most 50 Lloyd iterations. Labels are canonicalized by minimum
    node index. The requested K is capped at the number of active nodes.
    """
    if isinstance(communities, (bool, np.bool_)) or communities not in (2, 3):
        raise ValueError('communities must be 2 or 3')
    a = _adjacency(adjacency)
    strength = a.sum(axis=1)
    active = np.flatnonzero(strength > 0)
    labels = np.full(45, -1, dtype=int)
    if not len(active):
        return labels
    k = min(int(communities), len(active))
    scale = np.sqrt(strength[active])
    normalized = a[np.ix_(active, active)] / np.outer(scale, scale)
    _, vectors = np.linalg.eigh(normalized)
    points = vectors[:, -k:]
    norms = np.linalg.norm(points, axis=1)
    points = points / np.where(norms > 0, norms, 1)[:, None]
    centers = [points[0].copy()]
    selected = [0]
    for _ in range(1, k):
        distances = np.min(np.sum((points[:, None] - np.asarray(centers)) ** 2, axis=2), axis=1)
        distances[selected] = -1
        chosen = int(np.argmax(distances))
        selected.append(chosen)
        centers.append(points[chosen].copy())
    centers = np.asarray(centers)
    previous = None
    for _ in range(50):
        distances = np.sum((points[:, None] - centers) ** 2, axis=2)
        membership = np.argmin(distances, axis=1)
        if previous is not None and np.array_equal(membership, previous):
            break
        previous = membership.copy()
        for cluster in range(k):
            members = membership == cluster
            if members.any():
                centers[cluster] = points[members].mean(axis=0)
            else:
                # Farthest observed point, with stable low-index tie breaking.
                chosen = int(np.argmax(distances.min(axis=1)))
                centers[cluster] = points[chosen]
    present = sorted(np.unique(membership), key=lambda c: int(active[membership == c].min()))
    for canonical, cluster in enumerate(present):
        labels[active[membership == cluster]] = canonical
    return labels


def adjusted_rand(labels1, labels2):
    """Analytic ARI on common nonisolates; fewer than two shared nodes gives 0.

    Inferential callers must separately impose their declared support limit
    (at least 20 common nodes); this algebra helper does not hide small cases.
    """
    a, b = np.asarray(labels1), np.asarray(labels2)
    if a.ndim != 1 or a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Matching finite one-dimensional label arrays required')
    keep = (a >= 0) & (b >= 0)
    a, b = a[keep], b[keep]
    n = len(a)
    if n < 2:
        return 0.
    _, a = np.unique(a, return_inverse=True)
    _, b = np.unique(b, return_inverse=True)
    table = np.zeros((a.max() + 1, b.max() + 1), dtype=np.int64)
    np.add.at(table, (a, b), 1)
    choose2 = lambda counts: np.sum(counts * (counts - 1) / 2)
    joint = choose2(table)
    rows, columns = choose2(table.sum(axis=1)), choose2(table.sum(axis=0))
    expected = rows * columns / (n * (n - 1) / 2)
    denominator = (rows + columns) / 2 - expected
    return float((joint - expected) / denominator) if denominator else 1.


def relational_features(g, last_draw, communities=2):
    """Training-only neighbor, within-community, and clustering node features.

    Neighbor affinity averages residual edges to the last draw's other
    winners, divided by sqrt((f_i+5)*(f_j+5)). Within-community residual edge
    sums divide by 5*f_i+5; weighted spectral communities come from this graph.
    Every candidate is OLS-residualized against frequency then standardized.
    ``raw_features`` exposes the auditable pre-OLS definitions; weighted
    strength's frequency residual is analytically zero and never a candidate.
    """
    last = np.asarray(last_draw)
    if last.shape != (45,) or not np.isin(last, (0, 1)).all() or last.sum() != 6:
        raise ValueError('last_draw must contain exactly six binary winners among 45')
    f = _vector(g['frequency'], 'frequency')
    r = np.asarray(g['residual_adjacency'], dtype=float)
    if r.shape != (45, 45) or not np.isfinite(r).all():
        raise ValueError('Finite 45x45 residual adjacency required')
    labels = spectral_partition(g['adjacency'], communities)
    winners = np.flatnonzero(last)
    affinity = r[:, winners] / np.sqrt((f[:, None] + 5) * (f[winners][None, :] + 5))
    # r has zero diagonal, so self contributes zero and is excluded from n.
    neighbor = affinity.sum(axis=1) / (6 - last.astype(int))
    same = (labels[:, None] == labels[None, :]) & (labels[:, None] >= 0)
    community = (r * same).sum(axis=1) / (5 * f + 5)
    raw = dict(neighbor=neighbor, community=community,
               clustering=_vector(g['local_clustering'], 'local_clustering').copy())
    result = {name: standardize(residualize(values, f)) for name, values in raw.items()}
    result.update(labels=labels, raw_features=raw, strength_residual=np.zeros(45))
    return result
