"""Tensor algebra contracts, using only independently constructed synthetic data."""

import importlib.util

import numpy as np
import pytest


def test_tensor_decomposition_module_exists():
    assert importlib.util.find_spec('src.analysis.tensor_decomposition') is not None


def test_unfold_has_mode_first_and_remaining_axes_in_original_order():
    from src.analysis.tensor_decomposition import unfold
    x = np.arange(12).reshape(2, 3, 2)
    np.testing.assert_array_equal(unfold(x, 0), [[0, 1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11]])
    np.testing.assert_array_equal(unfold(x, 1), [[0, 1, 6, 7], [2, 3, 8, 9], [4, 5, 10, 11]])
    np.testing.assert_array_equal(unfold(x, 2), [[0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9, 11]])


@pytest.mark.parametrize('mode', [0, 1, 2])
def test_mode_product_contracts_the_specified_axis(mode):
    from src.analysis.tensor_decomposition import mode_product
    x = np.arange(24).reshape(2, 3, 4)
    matrix = np.arange(5 * x.shape[mode]).reshape(5, x.shape[mode])
    equations = ['ai,ijk->ajk', 'bj,ijk->ibk', 'ck,ijk->ijc']
    expected = np.einsum(equations[mode], matrix, x)
    np.testing.assert_allclose(mode_product(x, matrix, mode), expected)


def test_hosvd_full_thin_reconstruction_spectrum_and_core():
    from src.analysis.tensor_decomposition import hosvd
    x = np.random.default_rng(17).normal(size=(21, 5, 3))
    original = x.copy()
    result = hosvd(x)
    assert result['ranks'] == (15, 5, 3)
    np.testing.assert_allclose(result['reconstruction'], x, atol=2e-14)
    assert result['relative_error'] < 1e-14
    assert result['explained_energy'] == pytest.approx([1, 1, 1])
    expected_core = np.einsum('ijk,ia,jb,kc->abc', x, *result['factors'])
    np.testing.assert_allclose(result['core'], expected_core, atol=1e-14)
    for mode, (factor, values) in enumerate(zip(result['factors'], result['singular_values'])):
        assert factor.shape == (x.shape[mode], result['ranks'][mode])
        expected = np.linalg.svd(np.moveaxis(x, mode, 0).reshape(x.shape[mode], -1), compute_uv=False)
        np.testing.assert_allclose(values, expected, rtol=1e-12, atol=1e-14)
        np.testing.assert_allclose(factor.T @ factor, np.eye(factor.shape[1]), atol=1e-14)
        assert np.all(factor[np.argmax(abs(factor), axis=0), np.arange(factor.shape[1])] >= 0)
    np.testing.assert_array_equal(x, original)


def test_truncated_hosvd_has_full_spectra_and_energy_matches_projection():
    from src.analysis.tensor_decomposition import hosvd
    x = np.random.default_rng(18).normal(size=(15, 7, 4))
    result = hosvd(x, (3, 2, 2))
    expected = np.einsum('abc,ia,jb,kc->ijk', result['core'], *result['factors'])
    np.testing.assert_allclose(result['reconstruction'], expected, atol=1e-14)
    assert result['core'].shape == (3, 2, 2)
    assert [len(s) for s in result['singular_values']] == [15, 7, 4]
    for rank, values, energy in zip(result['ranks'], result['singular_values'], result['explained_energy']):
        assert energy == pytest.approx(np.sum(values[:rank] ** 2) / np.sum(values ** 2))
    residual = np.linalg.norm(x - expected) / np.linalg.norm(x)
    assert result['relative_error'] == pytest.approx(residual)
    assert residual**2 == pytest.approx(1 - np.sum(result['core']**2) / np.sum(x**2))


def test_maximum_rank_decomposition_can_be_sliced_for_smaller_rank_search():
    from src.analysis.tensor_decomposition import hosvd
    x = np.random.default_rng(19).normal(size=(20, 9, 5))
    maximum = hosvd(x, (8, 6, 3))
    smaller = hosvd(x, (4, 2, 1))
    expected = np.einsum('abc,ia,jb,kc->ijk', maximum['core'][:4, :2, :1],
                         maximum['factors'][0][:, :4], maximum['factors'][1][:, :2],
                         maximum['factors'][2][:, :1])
    np.testing.assert_allclose(smaller['reconstruction'], expected, atol=2e-14)


def test_exact_low_rank_recovery_compared_with_iid_full_rank():
    from src.analysis.tensor_decomposition import effective_rank, hosvd
    rng = np.random.default_rng(20)
    factors = [np.linalg.qr(rng.normal(size=(d, r)))[0] for d, r in [(30, 2), (12, 2), (5, 2)]]
    core = np.zeros((2, 2, 2))
    core[0, 0, 0], core[1, 1, 1] = 3, 2
    x = np.einsum('abc,ia,jb,kc->ijk', core, *factors)
    low = hosvd(x, (2, 2, 2))
    iid = hosvd(rng.normal(size=x.shape), (2, 2, 2))
    assert low['relative_error'] < 1e-14
    assert iid['relative_error'] > 0.8
    assert low['explained_energy'] == pytest.approx([1, 1, 1])
    assert effective_rank(low['singular_values'][0]) < 2
    assert effective_rank(iid['singular_values'][0]) > 15


def test_rank_one_and_repeated_spectra_are_finite_and_deterministic():
    from src.analysis.tensor_decomposition import hosvd
    for x in [np.ones((12, 5, 3)), np.eye(4)[:, :, None]]:
        first, second = hosvd(x), hosvd(x)
        np.testing.assert_allclose(first['reconstruction'], x, atol=1e-14)
        assert np.isfinite(first['core']).all()
        for a, b in zip(first['factors'], second['factors']):
            np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(first['core'], second['core'])


@pytest.mark.parametrize('x', [np.zeros((2, 3, 4)), np.ones((2, 3)), np.ones((2, 0, 3)),
                                  np.full((2, 3, 4), np.nan), np.full((2, 3, 4), np.inf),
                                  np.ones((2, 3, 4), dtype=complex) * 1j])
def test_hosvd_rejects_invalid_tensor(x):
    from src.analysis.tensor_decomposition import hosvd
    with pytest.raises(ValueError):
        hosvd(x)


@pytest.mark.parametrize('ranks', [(0, 2, 1), (4, 2, 1), (1, 4, 1), (1, 2, 3),
                                      (1, 2), (1.0, 2, 1), (True, 2, 1)])
def test_hosvd_rejects_invalid_ranks(ranks):
    from src.analysis.tensor_decomposition import hosvd
    with pytest.raises(ValueError):
        hosvd(np.ones((3, 3, 2)), ranks)


@pytest.mark.parametrize('mode', [-1, 3, 1.0, True])
def test_tensor_operations_reject_invalid_mode(mode):
    from src.analysis.tensor_decomposition import mode_product, unfold
    with pytest.raises(ValueError):
        unfold(np.ones((2, 3, 4)), mode)
    with pytest.raises(ValueError):
        mode_product(np.ones((2, 3, 4)), np.eye(3), mode)


@pytest.mark.parametrize('matrix', [np.ones((4, 4)), np.ones(3), np.full((1, 3), np.nan),
                                       np.empty((0, 3))])
def test_mode_product_rejects_bad_matrix(matrix):
    from src.analysis.tensor_decomposition import mode_product
    with pytest.raises(ValueError):
        mode_product(np.ones((2, 3, 4)), matrix, 1)


def test_entropy_and_effective_rank_use_squared_singular_values():
    from src.analysis.tensor_decomposition import effective_rank, spectral_entropy
    expected = -(0.8 * np.log(0.8) + 0.2 * np.log(0.2))
    assert spectral_entropy([2, 1, 0]) == pytest.approx(expected)
    assert effective_rank([2, 1, 0]) == pytest.approx(np.exp(expected))
    assert spectral_entropy([2, 1, 0], normalized=True) == pytest.approx(expected / np.log(3))
    assert spectral_entropy([2, 1, 0], normalized=True, dimension=5) == pytest.approx(expected / np.log(5))
    assert spectral_entropy([1]) == 0
    assert spectral_entropy([1], normalized=True) == 0
    assert effective_rank([5, 0, 0]) == 1
    assert effective_rank([1, 1, 1, 1]) == pytest.approx(4)
    assert spectral_entropy([2e200, 1e200]) == pytest.approx(expected)
    assert spectral_entropy([2e-200, 1e-200]) == pytest.approx(expected)


@pytest.mark.parametrize('values', [[], [0, 0], [-1, 2], [np.inf], [np.nan], [[1, 2]]])
def test_spectral_metrics_reject_undefined_spectra(values):
    from src.analysis.tensor_decomposition import effective_rank, spectral_entropy
    for function in [spectral_entropy, effective_rank]:
        with pytest.raises(ValueError):
            function(values)


def test_subspace_overlap_is_invariant_to_rotation_sign_and_scaling():
    from src.analysis.tensor_decomposition import subspace_similarity
    basis = np.eye(6)[:, :2]
    rotated = basis @ np.array([[0, -3], [2, 0]])
    assert subspace_similarity(basis, rotated) == pytest.approx(1)
    assert subspace_similarity(basis, np.eye(6)[:, 2:4]) == pytest.approx(0)
    partial = np.column_stack([np.eye(6)[:, 0], np.eye(6)[:, 2]])
    assert subspace_similarity(basis, partial) == pytest.approx(0.5)
    redundant = np.column_stack([basis[:, 0], basis[:, 0]])
    assert subspace_similarity(redundant, -redundant) == pytest.approx(1)


def test_procrustes_alignment_removes_rotation_and_preserves_candidate_gram():
    from src.analysis.tensor_decomposition import align_factors
    reference = np.linalg.qr(np.random.default_rng(21).normal(size=(12, 3)))[0]
    rotation = np.linalg.qr(np.random.default_rng(22).normal(size=(3, 3)))[0]
    candidate = reference @ rotation
    saved = candidate.copy()
    aligned = align_factors(reference, candidate)
    np.testing.assert_allclose(aligned, reference, atol=1e-14)
    np.testing.assert_allclose(aligned @ aligned.T, candidate @ candidate.T, atol=1e-14)
    np.testing.assert_array_equal(candidate, saved)


@pytest.mark.parametrize('a,b', [(np.ones((3, 2)), np.ones((4, 2))),
                                   (np.ones((3, 2)), np.ones((3, 1))),
                                   (np.ones(3), np.ones(3)),
                                   (np.ones((3, 2)), np.full((3, 2), np.nan))])
def test_factor_comparison_rejects_incompatible_arrays(a, b):
    from src.analysis.tensor_decomposition import align_factors, subspace_similarity
    for function in [align_factors, subspace_similarity]:
        with pytest.raises(ValueError):
            function(a, b)


def test_subspace_similarity_rejects_zero_or_unequal_numerical_rank():
    from src.analysis.tensor_decomposition import subspace_similarity
    with pytest.raises(ValueError):
        subspace_similarity(np.zeros((3, 2)), np.zeros((3, 2)))
    with pytest.raises(ValueError):
        subspace_similarity(np.eye(3)[:, :2], np.ones((3, 2)))
