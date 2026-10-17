"""Deterministic, thin HOSVD and rotation-invariant tensor diagnostics.

Axes retain their input order throughout: time, number, feature for the
Phase17 tensors. No observations, centering rules, or fitted scaling enter
this numerical module.
"""

from __future__ import annotations

import numpy as np
from scipy import linalg


def _real_array(value, ndim: int, name: str) -> np.ndarray:
    if np.iscomplexobj(value):
        raise ValueError(f'{name} must be real')
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{name} must be a real numeric array') from exc
    if array.ndim != ndim or not all(array.shape) or not np.isfinite(array).all():
        raise ValueError(f'{name} must be a nonempty finite {ndim}D array')
    return array


def _mode(mode: int) -> int:
    if isinstance(mode, (bool, np.bool_)) or not isinstance(mode, (int, np.integer)) or mode not in (0, 1, 2):
        raise ValueError('mode must be an integer in {0, 1, 2}')
    return int(mode)


def unfold(x, mode: int) -> np.ndarray:
    """Move ``mode`` to the rows; flatten the remaining axes in C order."""
    x = _real_array(x, 3, 'x')
    mode = _mode(mode)
    return np.moveaxis(x, mode, 0).reshape(x.shape[mode], -1)


def mode_product(x, matrix, mode: int) -> np.ndarray:
    """Contract one axis with a ``(new_dimension, old_dimension)`` matrix."""
    x = _real_array(x, 3, 'x')
    matrix = _real_array(matrix, 2, 'matrix')
    mode = _mode(mode)
    if matrix.shape[1] != x.shape[mode]:
        raise ValueError('matrix columns must match the selected tensor dimension')
    return np.moveaxis(np.tensordot(matrix, x, axes=(1, mode)), 0, mode)


def hosvd(x, ranks=None) -> dict:
    """Compute the truncated higher-order SVD of a finite, nonzero 3D tensor.

    ``ranks`` gives three positive integers, each at most that unfolding's
    thin dimension, ``min(axis_length, product(other_axis_lengths))``.
    With ``None`` all thin factors are retained, reconstructing the input
    to floating-point precision without a square temporal factor.

    Return factors (axis length by requested rank), full thin singular
    spectra, projected core, reconstruction, relative Frobenius error,
    per-mode retained squared energy, and the three ranks. Each factor
    column's largest absolute loading is positive; the core uses those
    same signed columns. Repeated singular values determine a subspace,
    rather than uniquely identifiable individual columns.

    To search nested ranks efficiently, decompose once at maximum ranks;
    slice the core on all three axes and the factors' columns to obtain
    every smaller reconstruction. Full spectra remain available for all
    concentration and entropy diagnostics.
    """
    x = _real_array(x, 3, 'x')
    scale = float(np.max(np.abs(x)))
    if scale == 0:
        raise ValueError('x must have positive energy')
    limits = tuple(min(d, x.size // d) for d in x.shape)
    if ranks is None:
        ranks = limits
    else:
        try:
            ranks = tuple(ranks)
        except TypeError as exc:
            raise ValueError('ranks must contain three positive integers') from exc
        if len(ranks) != 3 or any(
            isinstance(r, (bool, np.bool_)) or not isinstance(r, (int, np.integer))
            or not 1 <= r <= limit for r, limit in zip(ranks, limits)
        ):
            raise ValueError('ranks must be three positive integers within the thin mode dimensions')
        ranks = tuple(int(r) for r in ranks)

    # Scaling avoids squared-energy overflow/underflow without changing factors.
    scaled = x / scale
    factors, singular_values, explained_energy = [], [], []
    for mode, rank in enumerate(ranks):
        matrix = np.moveaxis(scaled, mode, 0).reshape(x.shape[mode], -1)
        left, values, _ = linalg.svd(matrix, full_matrices=False, check_finite=False)
        factor = left[:, :rank].copy()
        pivots = np.argmax(np.abs(factor), axis=0)
        signs = np.where(factor[pivots, np.arange(rank)] < 0, -1.0, 1.0)
        factor *= signs
        factors.append(factor)
        singular_values.append(values * scale)
        energy = float(np.dot(values[:rank], values[:rank]) / np.dot(values, values))
        explained_energy.append(float(np.clip(energy, 0, 1)))

    core = scaled
    for mode, factor in enumerate(factors):
        core = mode_product(core, factor.T, mode)
    reconstruction = core
    for mode, factor in enumerate(factors):
        reconstruction = mode_product(reconstruction, factor, mode)
    relative_error = float(np.linalg.norm(scaled - reconstruction) / np.linalg.norm(scaled))
    return {
        'factors': factors,
        'singular_values': singular_values,
        'core': core * scale,
        'reconstruction': reconstruction * scale,
        'relative_error': relative_error,
        'explained_energy': explained_energy,
        'ranks': ranks,
    }


def spectral_entropy(singular_values, normalized: bool = False, dimension=None) -> float:
    """Shannon entropy in nats of normalized squared singular values.

    Zero singular values contribute zero. The all-zero spectrum is
    undefined and rejected. For normalized entropy, divide by log of the
    supplied mode ``dimension`` (default: spectrum length); dimension one
    yields zero. Supplying the actual mode dimension matters for tall
    thin unfoldings whose spectrum is shorter than the tensor axis.
    """
    values = _real_array(singular_values, 1, 'singular_values')
    maximum = float(np.max(values))
    if np.any(values < 0) or maximum == 0:
        raise ValueError('singular_values must be nonnegative with positive energy')
    probabilities = (values / maximum) ** 2
    probabilities /= probabilities.sum()
    positive = probabilities[probabilities > 0]
    entropy = float(-np.dot(positive, np.log(positive)))
    if dimension is not None and (
        isinstance(dimension, (bool, np.bool_)) or not isinstance(dimension, (int, np.integer))
        or dimension < len(values)
    ):
        raise ValueError('dimension must be an integer at least as large as the spectrum length')
    if normalized:
        dimension = len(values) if dimension is None else dimension
        return entropy / float(np.log(dimension)) if dimension > 1 else 0.0
    return entropy


def effective_rank(singular_values) -> float:
    """Return exp(Shannon entropy) using normalized squared singular values."""
    return float(np.exp(spectral_entropy(singular_values)))


def _factor_pair(reference, candidate) -> tuple[np.ndarray, np.ndarray]:
    reference = _real_array(reference, 2, 'reference')
    candidate = _real_array(candidate, 2, 'candidate')
    if reference.shape != candidate.shape:
        raise ValueError('factor arrays must have the same shape')
    return reference, candidate


def _column_basis(matrix: np.ndarray) -> np.ndarray:
    # SVD removes redundant columns, unlike a QR completion that can inject
    # arbitrary directions into rank-deficient factors.
    matrix = matrix / max(float(np.max(np.abs(matrix))), np.finfo(float).tiny)
    left, values, _ = linalg.svd(matrix, full_matrices=False, check_finite=False)
    rank = int(np.sum(values > max(matrix.shape) * np.finfo(float).eps * values[0]))
    return left[:, :rank]


def subspace_similarity(a, b) -> float:
    """Mean squared principal-angle cosine, invariant to signs and rotations.

    Arrays must have identical shapes and equal positive numerical column
    rank. Redundant columns are removed using a reduced SVD. A zero or
    unequal-rank comparison is undefined here and raises ``ValueError``;
    consumers can apply the same exclusion rule to real and null data.
    """
    a, b = _factor_pair(a, b)
    qa, qb = _column_basis(a), _column_basis(b)
    if qa.shape[1] == 0 or qa.shape[1] != qb.shape[1]:
        raise ValueError('subspaces must have equal positive numerical rank')
    cosines = linalg.svdvals(qa.T @ qb, check_finite=False)
    return float(np.clip(np.mean(cosines ** 2), 0, 1))


def align_factors(reference, candidate) -> np.ndarray:
    """Rotate candidate toward reference by orthogonal Procrustes.

    Both factors must have the same shape. The returned candidate times
    an orthogonal matrix preserves its column subspace and row Gram
    matrix. Inputs are not changed. This handles arbitrary rotations,
    including signs and permutations, rather than comparing raw columns.
    """
    reference, candidate = _factor_pair(reference, candidate)
    reference_scale = max(float(np.max(np.abs(reference))), np.finfo(float).tiny)
    candidate_scale = max(float(np.max(np.abs(candidate))), np.finfo(float).tiny)
    left, _, right = linalg.svd(
        (candidate / candidate_scale).T @ (reference / reference_scale),
        full_matrices=False, check_finite=False,
    )
    return candidate @ (left @ right)
