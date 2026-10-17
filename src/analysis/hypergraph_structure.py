"""Causal six-number hypergraphs over the fixed 1..45 main-number universe.

Subset arrays use zero-based coordinates; public numbers and occurrence draw
indices are ONE-based. No four-number expansion or result fetching is used.
"""
from functools import lru_cache
from itertools import combinations
from math import comb
import numpy as np
from src.analysis.recurrence import research_matrix


TRIPLES = np.asarray(list(combinations(range(45), 3)), dtype=np.int16)
PAIRS = np.asarray(list(combinations(range(45), 2)), dtype=np.int16)
TRIPLES.setflags(write=False)
PAIRS.setflags(write=False)


def _size(size):
    if type(size) is not int or size not in (2, 3):
        raise ValueError('Only pair and triple subsets are supported')
    return size


@lru_cache(maxsize=2)
def _lookup(size):
    subsets = TRIPLES if _size(size) == 3 else PAIRS
    lookup = np.full((45,) * size, -1, dtype=np.int32)
    lookup[tuple(subsets.T)] = np.arange(len(subsets))
    lookup.setflags(write=False)
    return lookup


def _prefix(x, cutoff=None):
    # Require an exact supplied prefix: a cutoff cannot hide future rows.
    x = research_matrix(x)
    if cutoff is None:
        return x
    if type(cutoff) is not int or cutoff != len(x):
        raise ValueError('Cutoff must equal the supplied completed prefix length')
    return x


def _window(x, window):
    window = len(x) if window is None else window
    if type(window) is not int or not 1 <= window <= len(x):
        raise ValueError('A full positive integer window is required')
    return window


def binary_hyperedges(x, cutoff=None):
    """Return sorted ONE-based main numbers, shape (completed draws, 6)."""
    x = _prefix(x, cutoff)
    return np.nonzero(x)[1].reshape(-1, 6) + 1


@lru_cache(maxsize=16)
def _ids(binary_rows, length, size):
    x = np.frombuffer(binary_rows, dtype=np.bool_).reshape(length, 45)
    numbers = np.nonzero(x)[1].reshape(-1, 6)
    slots = np.asarray(list(combinations(range(6), size)))
    values = numbers[:, slots]
    result = _lookup(size)[tuple(values[..., i] for i in range(size))]
    result.setflags(write=False)
    return result


def subset_ids(x, size=3):
    """Map each draw to its 20 triple IDs (or 15 pair IDs), in lexical order."""
    x = _prefix(x)
    _size(size)
    return _ids(x.tobytes(), len(x), size)


def subset_counts(x, window=None, cutoff=None, size=3):
    """Count subsets in the last complete window of a completed prefix.

    Expected counts and z scores use the uniform six-of-45 reference model;
    they are descriptive quantities, not corrected significance claims.
    """
    x = _prefix(x, cutoff)
    window = _window(x, window)
    subsets = TRIPLES if _size(size) == 3 else PAIRS
    ids = subset_ids(x, size)[-window:]
    counts = np.bincount(ids.ravel(), minlength=len(subsets))
    frequency = x[-window:].sum(0).astype(int)
    participation = np.bincount(subsets.ravel(), weights=np.repeat(counts, size),
                                minlength=45).astype(int)
    probability = comb(6, size) / comb(45, size)
    expected = window * probability
    return dict(counts=counts, support=counts.copy(), subsets=subsets,
                frequency=frequency, node_participation=participation,
                window=window, cutoff=len(x), expected=expected,
                probability=probability, lift=counts / expected,
                normalized=(counts - expected) / np.sqrt(expected * (1 - probability)),
                subset_ids=ids)


def _numbers(subset, sizes):
    numbers = np.asarray(subset)
    if (numbers.ndim != 1 or len(numbers) not in sizes or
            not np.issubdtype(numbers.dtype, np.integer) or
            not np.all((numbers >= 1) & (numbers <= 45)) or
            not np.all(np.diff(numbers) > 0)):
        raise ValueError('Ascending distinct integer main numbers in 1..45 required')
    return numbers.astype(int)


def motif_diagnostic(x, subset, window=None, cutoff=None):
    """Describe one pair/triple and disjoint recent-versus-prior recurrence."""
    x = _prefix(x, cutoff)
    numbers = _numbers(subset, (2, 3))
    window = _window(x, window)
    present = x[:, numbers - 1].all(1)
    start = len(x) - window
    occurrences = (np.flatnonzero(present[start:]) + start + 1).tolist()
    count = len(occurrences)
    prior_count = int(present[:start].sum())
    probability = comb(6, len(numbers)) / comb(45, len(numbers))
    expected = window * probability
    return dict(subset=numbers.tolist(), occurrences=occurrences, count=count,
                expected=expected, lift=count / expected,
                normalized=(count - expected) / np.sqrt(expected * (1 - probability)),
                recurrence_intervals=np.diff(occurrences).tolist(), window=window,
                cutoff=len(x), recent_count=count, recent_rate=count / window,
                longterm_count=prior_count, longterm_window=start,
                longterm_rate=prior_count / start if start else 0.,
                trend=count / window - prior_count / start if start else 0.)


def continuation_scores(x, window, support=2, shrinkage=5):
    """Conditional motif continuation above each candidate's own window rate.

    Contexts are pairs in the last completed draw, excluding the candidate.
    Both pair and triple must meet support. Shrink conditional rates towards
    the candidate's own rate, then average weighted differences across eligible
    contexts. Candidates with no eligible context receive exactly zero.
    """
    x = _prefix(x)
    window = _window(x, window)
    if type(support) is not int or support not in (2, 3):
        raise ValueError('Predeclared support must be 2 or 3')
    if (isinstance(shrinkage, (bool, np.bool_)) or not np.isscalar(shrinkage) or
            not np.isfinite(shrinkage) or shrinkage <= 0):
        raise ValueError('Positive finite shrinkage required')
    triple_counts = subset_counts(x, window=window)
    pair_counts = subset_counts(x, window=window, size=2)
    last = np.flatnonzero(x[-1])
    pairs = np.asarray(list(combinations(last, 2)))
    cp = pair_counts['counts'][_lookup(2)[tuple(pairs.T)]]
    candidates = np.arange(45)[:, None]
    triples = np.sort(np.concatenate((np.broadcast_to(pairs, (45, 15, 2)),
                                     np.broadcast_to(candidates[..., None], (45, 15, 1))), axis=2), axis=2)
    triple_ids = _lookup(3)[tuple(triples[..., i] for i in range(3))]
    valid = (candidates != pairs[:, 0]) & (candidates != pairs[:, 1])
    ct = triple_counts['counts'][np.maximum(triple_ids, 0)]
    valid &= (ct >= support) & (cp[None, :] >= support)
    own_rate = triple_counts['frequency'] / window
    conditional = (ct + shrinkage * own_rate[:, None]) / (cp + shrinkage)
    weight = cp / (cp + shrinkage)
    differences = (conditional - own_rate[:, None]) * weight
    eligible = valid.sum(1)
    raw = np.where(valid, differences, 0.).sum(1) / np.maximum(eligible, 1)
    diagnostics = []
    for number in range(45):
        contexts = [dict(pair=(pairs[k] + 1).tolist(), c_pair=int(cp[k]),
                         c_triple=int(ct[number, k]), conditional=float(conditional[number, k]),
                         weight=float(weight[k])) for k in np.flatnonzero(valid[number])]
        diagnostics.append(dict(number=number + 1,
                                own_frequency=int(triple_counts['frequency'][number]),
                                contexts=contexts, score=float(raw[number])))
    return dict(raw_scores=raw, diagnostics=diagnostics, counts=triple_counts,
                pair_counts=pair_counts, window=window, support=support, shrinkage=shrinkage)


def set_similarity(a, b):
    """Exact overlap and Jaccard similarity of two sorted six-number draws."""
    a, b = _numbers(a, (6,)), _numbers(b, (6,))
    overlap = int(np.intersect1d(a, b).size)
    return dict(overlap=overlap, jaccard=overlap / (12 - overlap))


def pairwise_overlap(x):
    """All draw similarities, including a six/one overlap/Jaccard diagonal."""
    x = _prefix(x).astype(np.int16)
    overlap = x @ x.T
    return dict(overlap=overlap, jaccard=overlap / (12 - overlap))
