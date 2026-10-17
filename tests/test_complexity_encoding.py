"""Hand-checked encodings and finite-sequence complexity proxies for H14."""
import importlib.util
import struct

import numpy as np
import pytest

from src.analysis.spatiotemporal import constrained_surrogate, iid_surrogate, lotto_matrix


def _two_draws():
    x = np.zeros((2, 45), dtype=bool)
    x[0, [0, 1, 2, 3, 4, 5]] = True
    x[1, [0, 8, 16, 24, 32, 44]] = True
    return x


def test_encoding_module_exists():
    assert importlib.util.find_spec('src.analysis.complexity_encoding') is not None


def test_representations_have_all_declared_families_and_symbol_counts():
    from src.analysis.complexity_encoding import representations
    result = representations(_two_draws(), cutoff=2)
    assert set(result) == {f'number{i:02d}' for i in range(1, 46)} | {
        'full_binary', 'draw_packed', 'sorted_numbers', 'adjacent_gaps',
        'sum', 'range', 'std', 'spacing_std'}
    assert sum(r['binary'] for r in result.values()) == 46
    assert {name for name, r in result.items() if r['scalar']} == {
        'sum', 'range', 'std', 'spacing_std'}
    expected = {'full_binary': (90, 90, 2), 'draw_packed': (12, 12, 256),
                'sorted_numbers': (12, 12, 45), 'adjacent_gaps': (10, 10, 44),
                'sum': (2, 4, 235), 'range': (2, 2, 40),
                'std': (2, 16, None), 'spacing_std': (2, 16, None)}
    for name, rep in result.items():
        n, raw_bytes, alphabet = expected.get(name, (2, 2, 2))
        assert rep['symbols'].shape == (n,)
        assert rep['N'] == rep['symbols_count'] == n
        assert rep['draws'] == 2
        assert len(rep['data']) == raw_bytes
        assert rep['alphabet'] == alphabet


def test_serialization_preserves_rows_number_order_padding_and_little_endian():
    from src.analysis.complexity_encoding import representations
    x = _two_draws()
    result = representations(x)
    assert result['number01']['data'] == bytes([1, 1])
    assert result['number02']['data'] == bytes([1, 0])
    assert result['number45']['data'] == bytes([0, 1])
    assert result['full_binary']['data'] == bytes(x.astype(np.uint8).ravel())
    assert result['draw_packed']['data'] == bytes([252, 0, 0, 0, 0, 0,
                                                    128, 128, 128, 128, 128, 8])
    assert result['draw_packed']['block_symbols'] == 6
    assert all(b & 7 == 0 for b in result['draw_packed']['data'][5::6])
    assert result['sorted_numbers']['data'] == bytes([1, 2, 3, 4, 5, 6,
                                                       1, 9, 17, 25, 33, 45])
    assert result['adjacent_gaps']['data'] == bytes([1, 1, 1, 1, 1, 8, 8, 8, 8, 12])
    assert result['sum']['data'] == bytes([21, 0, 130, 0])
    assert result['range']['data'] == bytes([5, 44])
    assert result['std']['symbols'][0] == pytest.approx(np.sqrt(35 / 12))
    assert result['spacing_std']['symbols'][1] == pytest.approx(1.6)
    assert result['spacing_std']['data'][:8] == bytes(8)
    assert struct.unpack('<dd', result['spacing_std']['data']) == pytest.approx((0., 1.6))
    assert result['std']['data'] == struct.pack('<dd', *result['std']['symbols'])


@pytest.mark.parametrize('cutoff', [1, 3, True, 2.0, 1246])
def test_representations_reject_cutoff_mismatch_instead_of_slicing(cutoff):
    from src.analysis.complexity_encoding import representations
    with pytest.raises(ValueError):
        representations(_two_draws(), cutoff=cutoff)


@pytest.mark.parametrize('x', [np.zeros((1, 45)), np.zeros((1246, 45)),
                                  np.zeros((2, 44)), np.ones((2, 45)),
                                  np.full((2, 45), np.nan)])
def test_representations_reject_nonresearch_matrices(x):
    from src.analysis.complexity_encoding import representations
    with pytest.raises(ValueError):
        representations(x)


@pytest.mark.parametrize('symbols,phrases', [([0], 1), ([0, 0], 2),
    ([0, 0, 0], 2), ([0, 0, 0, 0], 3), ([0, 1, 0, 1], 3),
    ([0, 1, 0, 1, 0, 1], 4), ([0, 1, 2, 3], 4)])
def test_lz78_hand_parsing_counts_unfinished_suffix(symbols, phrases):
    from src.analysis.complexity_encoding import lz78
    result = lz78(symbols, alphabet=4)
    assert result['phrases'] == phrases
    assert result['symbols'] == len(symbols)
    assert result['normalized'] == pytest.approx(phrases * np.log(len(symbols)) / np.log(4) / len(symbols))


def test_lz78_constant_periodic_and_iid_ordering_with_fixed_alphabet():
    from src.analysis.complexity_encoding import lz78
    constant = np.zeros(4000, dtype=np.uint8)
    periodic = np.tile(np.arange(4, dtype=np.uint8), 1000)
    iid = np.random.default_rng(16016).integers(0, 4, 4000, dtype=np.uint8)
    values = [lz78(sequence, alphabet=4)['normalized'] for sequence in (constant, periodic, iid)]
    assert 0 < values[0] < values[1] < values[2]
    # Alphabet is declared, even if the observed sequence occupies one category.
    assert lz78(constant, alphabet=2)['normalized'] == pytest.approx(2 * values[0])


@pytest.mark.parametrize('symbols,alphabet', [([], 2), ([[0, 1]], 2),
    ([0, np.nan], 2), ([0.5, 1.5], 2), ([0, 1], 1), ([0, 1], True),
    ([0, 1], 2.0), ([0, 1, 2], 2)])
def test_lz78_rejects_invalid_sequences_and_alphabets(symbols, alphabet):
    from src.analysis.complexity_encoding import lz78
    with pytest.raises(ValueError):
        lz78(symbols, alphabet)


@pytest.mark.parametrize('compressor', ['zlib', 'bz2', 'lzma'])
def test_compression_fixed_preset_lengths_roundtrip_and_symbol_denominator(compressor):
    import bz2
    import lzma
    import zlib
    from src.analysis.complexity_encoding import compression
    data = bytes([0, 1, 2, 3]) * 300
    compressed = {'zlib': lambda: zlib.compress(data, level=9),
                  'bz2': lambda: bz2.compress(data, compresslevel=9),
                  'lzma': lambda: lzma.compress(data, format=lzma.FORMAT_XZ, preset=0)}[compressor]()
    result = compression(data, compressor, symbol_count=600)
    assert result == compression(data, compressor, symbol_count=600)
    assert result['compressor'] == compressor
    assert result['raw_bytes'] == 1200
    assert result['compressed_bytes'] == len(compressed)
    assert result['ratio'] == pytest.approx(len(compressed) / 1200)
    assert result['bits_per_symbol'] == pytest.approx(8 * len(compressed) / 600)
    assert compression(data, compressor)['bits_per_symbol'] == pytest.approx(8 * len(compressed) / 1200)


@pytest.mark.parametrize('compressor', ['zlib', 'bz2', 'lzma'])
def test_compression_detects_repeated_sequence_against_random_bytes(compressor):
    from src.analysis.complexity_encoding import compression
    ordered = np.tile(np.arange(256, dtype=np.uint8), 32).tobytes()
    random = np.random.default_rng(16).integers(0, 256, 8192, dtype=np.uint8).tobytes()
    assert compression(ordered, compressor)['ratio'] < compression(random, compressor)['ratio']


@pytest.mark.parametrize('data,compressor,symbol_count', [
    (b'', 'zlib', None), (b'a', 'unknown', None), ('text', 'zlib', None),
    (b'a', 'zlib', 0), (b'a', 'zlib', True), (b'a', 'zlib', 1.0)])
def test_compression_rejects_invalid_bytes_compressors_and_symbol_counts(data, compressor, symbol_count):
    from src.analysis.complexity_encoding import compression
    with pytest.raises(ValueError):
        compression(data, compressor, symbol_count=symbol_count)


def test_temporal_shuffle_preserves_whole_rows_and_margins_reproducibly():
    from src.analysis.complexity_encoding import temporal_shuffle
    x = iid_surrogate(104, seed=16)
    original = x.copy()
    shuffled = temporal_shuffle(x, seed=1616)
    np.testing.assert_array_equal(shuffled, temporal_shuffle(x, seed=1616))
    assert sorted(map(bytes, shuffled)) == sorted(map(bytes, x))
    np.testing.assert_array_equal(shuffled.sum(0), x.sum(0))
    np.testing.assert_array_equal(shuffled.sum(1), np.full(104, 6))
    np.testing.assert_array_equal(x, original)
    assert not np.shares_memory(x, shuffled)
    assert not np.array_equal(x, shuffled)
    with pytest.raises(ValueError):
        temporal_shuffle(np.tile(x[:1], (1246, 1)), seed=16)


def test_real_iid_and_fixed_margins_have_identical_encoding_lengths_and_repeatability():
    import pandas as pd
    from src.analysis.complexity_encoding import compression, representations
    history = pd.read_csv('data/raw/lotto_history.csv').iloc[:104]
    real = lotto_matrix(history, cutoff=104)
    histories = [real, iid_surrogate(104, seed=16),
                 constrained_surrogate(real, seed=16, trades_per_row=1)]
    reference = representations(real)
    for x in histories:
        first, repeated = representations(x), representations(x.copy())
        for name in reference:
            assert len(first[name]['data']) == len(reference[name]['data'])
            assert first[name]['N'] == reference[name]['N']
            assert first[name]['data'] == repeated[name]['data']
        for compressor in ('zlib', 'bz2', 'lzma'):
            assert compression(first['draw_packed']['data'], compressor) == compression(repeated['draw_packed']['data'], compressor)
