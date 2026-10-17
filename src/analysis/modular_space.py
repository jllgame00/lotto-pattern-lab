"""Phase15 finite-population residue summaries and causal successor tables.

Residue columns are numbered 0..k-1 and number columns represent 1..45.
No routine silently truncates an input prefix or wraps a temporal lag.
"""
import numpy as np

from src.analysis.recurrence import research_matrix


MODULI = (2, 3, 4, 5, 6, 7)
LAGS = (1, 2, 3, 4, 8, 13, 26)


def _integer(value):
    return isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_))


def representation(x, k, cutoff=None):
    """Return per-draw residue summaries with exact Lotto IID moments.

    ``cutoff`` denotes the last completed draw and must equal the input length.
    Arrays are newly allocated, including finite-population reference moments.
    Imbalance divides each draw's deviation by its IID standard deviation.
    """
    x = research_matrix(x)
    if not _integer(k) or k not in MODULI:
        raise ValueError('Modulus must be one of the predeclared values 2..7')
    if cutoff is not None and (not _integer(cutoff) or cutoff != len(x)):
        raise ValueError('Cutoff must equal the exact completed input prefix')

    residues = np.arange(1, 46) % k
    populations = np.bincount(residues, minlength=k)
    p = populations / 45.0
    expected = 6 * p
    covariance = 6 * 39/44 * (np.diag(p) - np.outer(p, p))
    histogram = np.column_stack([x[:, residues == r].sum(axis=1) for r in range(k)])
    frequencies = histogram / 6.0
    log_frequencies = np.zeros_like(frequencies)
    np.log2(frequencies, out=log_frequencies, where=frequencies > 0)
    occupied = (histogram > 0).sum(axis=1)
    return {
        'histogram': histogram,
        'populations': populations,
        'expected': expected,
        'covariance': covariance,
        'occupied': occupied,
        'concentration': np.square(frequencies).sum(axis=1),
        'entropy': -(frequencies * log_frequencies).sum(axis=1),
        'repeats': 6 - occupied,
        'repeated_classes': (histogram >= 2).sum(axis=1),
        'imbalance': (histogram - expected) / np.sqrt(np.diag(covariance)),
    }


def lagged(hist, lag):
    """Copy aligned source and future histograms, with no circular wrap."""
    hist = np.asarray(hist)
    if not _integer(lag) or lag not in LAGS:
        raise ValueError('Lag must be one of the predeclared temporal lags')
    if (hist.ndim != 2 or hist.shape[1] not in MODULI or len(hist) <= lag
            or not np.isfinite(hist).all() or not np.isin(hist, np.arange(7)).all()
            or not np.all(hist.sum(axis=1) == 6)):
        raise ValueError('Lag requires six-number residue histograms and a future pair')
    return hist[:-lag].copy(), hist[lag:].copy()


def transition(x, k, lag, cutoff=None):
    """Condition each future residue count on its source count (states 0..6).

    Counts and sums have shape (k, 7). The baseline and population variance
    use only the aligned future segment. Absent conditional means and all
    ineligible z statistics are NaN; ``eligible`` records the support filter.
    The z denominator includes the baseline's shared-sample correction.
    """
    source, future = lagged(representation(x, k, cutoff=cutoff)['histogram'], lag)
    sample_count = len(future)
    counts = np.empty((k, 7), dtype=np.int64)
    sums = np.empty_like(counts)
    for r in range(k):
        counts[r] = np.bincount(source[:, r].astype(int), minlength=7)
        sums[r] = np.bincount(source[:, r].astype(int), weights=future[:, r], minlength=7).astype(np.int64)
    conditional_means = np.full((k, 7), np.nan)
    np.divide(sums, counts, out=conditional_means, where=counts > 0)
    baseline = future.mean(axis=0)
    variance = future.var(axis=0, ddof=0)
    eligible = (counts >= 20) & (counts < sample_count) & (variance[:, None] > 0)
    inverse_count = np.zeros((k, 7))
    np.divide(1.0, counts, out=inverse_count, where=counts > 0)
    denominator = np.sqrt(np.maximum(variance[:, None] * (inverse_count - 1/sample_count), 0))
    z = np.full((k, 7), np.nan)
    np.divide(conditional_means - baseline[:, None], denominator, out=z, where=eligible)
    return {
        'counts': counts,
        'sums': sums,
        'conditional_means': conditional_means,
        'baseline': baseline,
        'variance': variance,
        'z': z,
        'eligible': eligible,
        'source': source,
        'future': future,
        'sample_count': sample_count,
    }
