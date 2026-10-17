"""Centered singular spectrum analysis and exploratory oscillatory candidates.

No scaling, data loading, significance test, or training cutoff is implicit here.
Callers supply only their training history and calibrate candidate scores against
the complete search under a null; a similar-energy pair alone is not evidence.
"""
from numbers import Integral

import numpy as np
from scipy.linalg import eigh


WINDOWS = (26, 52, 104)


def _integer(value, name, minimum=1):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)


def _series(x):
    values = np.asarray(x, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError('Expected a finite nonempty one-dimensional series')
    return values


def hankel(x, L):
    """Return the L by (N-L+1) trajectory matrix, with 2 <= L <= N/2."""
    values = _series(x)
    L = _integer(L, 'L', 2)
    if 2 * L > len(values):
        raise ValueError('L must be <= N/2')
    return np.lib.stride_tricks.sliding_window_view(values, L).T.copy()


def diagonal_average(matrix):
    """Average each anti-diagonal of a nonempty finite rectangular matrix."""
    a = np.asarray(matrix, dtype=float)
    if a.ndim != 2 or not a.size or not np.isfinite(a).all():
        raise ValueError('Expected a finite nonempty two-dimensional matrix')
    rows, columns = a.shape
    sums = np.zeros(rows + columns - 1)
    for i, row in enumerate(a):
        sums[i:i + columns] += row
    return sums / np.convolve(np.ones(rows), np.ones(columns))


def decompose(x, L, components=8):
    """Decompose a centered series into elementary reconstructed components.

    Eigh of H H.T is equivalent to the trajectory SVD: its eigenvalues are
    squared singular values and its eigenvectors are the left singular vectors.
    Computing H.T U only for the requested vectors avoids a full right SVD.
    All L singular values/energy ratios are returned in descending order;
    covariance roundoff can erase singular values near machine precision.
    ``right_vectors`` contains the leading rows of V.T, shape (r, N-L+1).
    Components retain input units; add ``mean`` once to their sum. Residual
    variance is the population variance after that centered reconstruction.
    """
    values = _series(x)
    mean = float(values.mean())
    centered = values - mean
    if np.ptp(values) == 0:
        centered = np.zeros_like(values)
    trajectory = hankel(centered, L)
    count = _integer(components, 'components')
    if count > L:
        raise ValueError('components must be <= L')
    eigenvalues, vectors = eigh(trajectory @ trajectory.T, check_finite=False,
                                overwrite_a=True, driver='evd')
    eigenvalues = np.maximum(eigenvalues[::-1], 0)
    # Discard covariance roundoff at the numerical rank boundary.
    eigenvalues[eigenvalues < np.finfo(float).eps * L * eigenvalues[0]] = 0
    singular_values = np.sqrt(eigenvalues)
    left = vectors[:, ::-1][:, :count].copy()
    projections = left.T @ trajectory
    right = np.divide(projections, singular_values[:count, None],
                      out=np.zeros_like(projections), where=singular_values[:count, None] > 0)
    weights = np.convolve(np.ones(L), np.ones(trajectory.shape[1]))
    reconstructed = np.array([np.convolve(left[:, i], projections[i]) / weights
                              for i in range(count)])
    total = float(eigenvalues.sum())
    return dict(singular_values=singular_values,
                energy_ratios=eigenvalues / total if total else np.zeros(L),
                components=reconstructed, mean=mean,
                residual_variance=float(np.var(centered - reconstructed.sum(axis=0))),
                left_vectors=left, right_vectors=right, window=int(L), n=len(values))


def _spectrum(component):
    power = np.abs(np.fft.rfft(component - component.mean())) ** 2
    power[0] = 0
    total = float(power.sum())
    if total <= 0:
        return np.inf, 0.
    peak = int(np.argmax(power))
    return len(component) / peak, float(power[peak] / total)


def candidate_pairs(result, min_period=8, max_period=104):
    """Return adjacent exploratory pairs among the first eight components.

    Require eigenenergy balance >= .7, dominant Fourier periods agreeing
    within 20%, and each component's peak spectral concentration >= .35.
    ``amplitude`` is the population standard deviation of the pair sum, in
    input units, not a sinusoid's peak height. Indices are zero based. The
    score is energy share * energy balance * minimum spectral concentration.
    Candidates need search-wide null calibration before interpretation.
    """
    if not np.isfinite([min_period, max_period]).all() or not 0 < min_period <= max_period:
        raise ValueError('Expected 0 < min_period <= max_period')
    components = np.asarray(result['components'], dtype=float)
    energies = np.asarray(result['energy_ratios'], dtype=float)
    limit = min(8, len(components), len(energies))
    spectra = [_spectrum(c) for c in components[:limit]]
    pairs = []
    for first in range(limit - 1):
        second = first + 1
        e1, e2 = energies[first:second + 1]
        if e1 <= 0 or e2 <= 0:
            continue
        balance = min(e1, e2) / max(e1, e2)
        p1, concentration1 = spectra[first]
        p2, concentration2 = spectra[second]
        concentration = min(concentration1, concentration2)
        if balance < .7 or concentration < .35:
            continue
        if not (min_period <= p1 <= max_period and min_period <= p2 <= max_period):
            continue
        if abs(p1 - p2) / max(p1, p2) > .2:
            continue
        energy = float(e1 + e2)
        pairs.append(dict(first=first, second=second, period=float((p1 + p2) / 2),
                          energy_share=energy,
                          amplitude=float(np.std(components[first] + components[second])),
                          spectral_concentration=concentration,
                          score=float(energy * balance * concentration)))
    return pairs


def recurrent_forecast(result, indices, steps=1):
    """Return ``steps`` forecasts using the standard SSA linear recurrence.

    For selected left vectors U_i, pi_i is their last coordinate and
    R = sum(pi_i U_i[:-1]) / (1-sum(pi_i**2)). Apply R chronologically to
    the last L-1 centered reconstructed values and restore the training mean.
    Near-singular subspaces (denominator <= .05) are rejected as unstable.
    """
    steps = _integer(steps, 'steps')
    components = np.asarray(result['components'], dtype=float)
    selected = list(indices)
    if not selected or any(isinstance(i, (bool, np.bool_)) or not isinstance(i, Integral)
                           or i < 0 or i >= len(components) for i in selected):
        raise ValueError('indices must select existing components')
    if len(set(selected)) != len(selected):
        raise ValueError('indices must be unique')
    left = np.asarray(result['left_vectors'], dtype=float)[:, selected]
    last = left[-1]
    denominator = 1 - float(last @ last)
    if denominator <= .05:
        raise ValueError('unstable SSA recurrence denominator')
    coefficients = (left[:-1] @ last) / denominator
    if not np.isfinite(coefficients).all() or np.linalg.norm(coefficients) > 10:
        raise ValueError('unstable SSA recurrence coefficients')
    width = len(coefficients)
    history = list(components[selected].sum(axis=0)[-width:])
    predictions = np.empty(steps)
    for i in range(steps):
        forecast = float(coefficients @ history[-width:])
        if not np.isfinite(forecast):
            raise ValueError('unstable SSA forecast')
        history.append(forecast)
        predictions[i] = forecast + result['mean']
    return predictions
