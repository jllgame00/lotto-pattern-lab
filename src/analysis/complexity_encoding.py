"""Fixed H14 representations and finite-sequence complexity proxies.

These encoding-dependent statistics do not measure true Kolmogorov complexity.
Every serialized byte stream keeps row order and uses the same encoding for
observed and null histories. Numeric multibyte fields are little-endian.
"""
import bz2
import lzma
import math
import zlib

import numpy as np

from src.analysis.recurrence import research_matrix


COMPRESSORS = ('zlib', 'bz2', 'lzma')


def representations(x, cutoff=None):
    """Encode exactly the supplied 2..1245 six-of-45 research draws.

    ``cutoff``, if given, must equal the input length; future suffixes are
    rejected rather than silently trimmed. Each record has one-dimensional
    ``symbols``, serialized ``data``, a declared ``alphabet`` (None for
    continuous scalars), ``binary``/``scalar`` flags, ``draws``, and matching
    symbol counts ``N`` and ``symbols_count``. ``block_symbols`` identifies
    the per-draw boundary for concatenated encodings, especially packed bytes.
    """
    x = research_matrix(x)
    if cutoff is not None and (
            isinstance(cutoff, (bool, np.bool_))
            or not isinstance(cutoff, (int, np.integer)) or cutoff != len(x)):
        raise ValueError('Cutoff must exactly match the supplied research history')
    result = {}

    def add(name, values, dtype, alphabet, *, binary=False, scalar=False,
            block_symbols=1):
        symbols = np.array(values, dtype=dtype, copy=True).ravel()
        result[name] = dict(symbols=symbols, data=symbols.tobytes(order='C'),
                            alphabet=alphabet, binary=binary, scalar=scalar,
                            draws=len(x), N=int(symbols.size),
                            symbols_count=int(symbols.size),
                            block_symbols=block_symbols)

    for number in range(45):
        add(f'number{number + 1:02d}', x[:, number], np.uint8, 2, binary=True)
    add('full_binary', x, np.uint8, 2, binary=True, block_symbols=45)
    add('draw_packed', np.packbits(x, axis=1, bitorder='big'), np.uint8, 256,
        block_symbols=6)
    numbers = (np.nonzero(x)[1] + 1).reshape(len(x), 6)
    gaps = np.diff(numbers, axis=1)
    add('sorted_numbers', numbers, np.uint8, 45, block_symbols=6)
    add('adjacent_gaps', gaps, np.uint8, 44, block_symbols=5)
    add('sum', numbers.sum(axis=1), '<u2', 235, scalar=True)
    add('range', numbers[:, -1] - numbers[:, 0], np.uint8, 40, scalar=True)
    add('std', numbers.std(axis=1, ddof=0), '<f8', None, scalar=True)
    add('spacing_std', gaps.std(axis=1, ddof=0), '<f8', None, scalar=True)
    return result


def lz78(symbols, alphabet):
    """Return deterministic LZ78 phrase count and ``c*log_q(N)/N``.

    A new phrase adds one trie edge and resets to the root. An unfinished
    final suffix counts as one further phrase. The alphabet q is declared
    rather than inferred from occupied categories. Integer category labels
    need not start at zero (e.g. sorted numbers use labels 1..45).
    Parsing uses expected O(N) time and at most O(N) trie edges.
    """
    if (isinstance(alphabet, (bool, np.bool_))
            or not isinstance(alphabet, (int, np.integer)) or alphabet < 2):
        raise ValueError('Declared alphabet must be an integer >= 2')
    symbols = np.asarray(symbols)
    if symbols.ndim != 1 or not symbols.size or symbols.dtype.kind not in 'biu':
        raise ValueError('LZ78 requires a nonempty one-dimensional integer sequence')
    values = symbols.tolist()
    if len(set(values)) > alphabet:
        raise ValueError('Occupied symbols exceed the declared alphabet')
    trie = [{}]
    node = 0
    phrases = 0
    for symbol in values:
        following = trie[node].get(symbol)
        if following is None:
            trie[node][symbol] = len(trie)
            trie.append({})
            phrases += 1
            node = 0
        else:
            node = following
    if node:
        phrases += 1
    n = int(symbols.size)
    return dict(phrases=phrases, normalized=phrases * math.log(n, alphabet) / n,
                symbols=n)


def compression(data, compressor, symbol_count=None):
    """Compress nonempty bytes using the fixed predeclared stdlib presets.

    Ratio is compressed/raw bytes, including compressor headers. The symbol
    denominator defaults to byte count; callers must supply it for multibyte
    numeric scalars. Absolute short-stream ratios include framing overhead.
    """
    if not isinstance(data, bytes) or not data:
        raise ValueError('Compression requires nonempty serialized bytes')
    if compressor not in COMPRESSORS:
        raise ValueError('Compressor must be zlib, bz2, or lzma')
    if symbol_count is None:
        symbol_count = len(data)
    if (isinstance(symbol_count, (bool, np.bool_))
            or not isinstance(symbol_count, (int, np.integer)) or symbol_count < 1):
        raise ValueError('Symbol count must be a positive integer')
    if compressor == 'zlib':
        compressed = zlib.compress(data, level=9)
    elif compressor == 'bz2':
        compressed = bz2.compress(data, compresslevel=9)
    else:
        compressed = lzma.compress(data, format=lzma.FORMAT_XZ, preset=0)
    size = len(compressed)
    return dict(compressor=compressor, raw_bytes=len(data), compressed_bytes=size,
                ratio=size / len(data), bits_per_symbol=8 * size / symbol_count)


def temporal_shuffle(x, seed):
    """Reorder complete research draws reproducibly, preserving both margins."""
    x = research_matrix(x)
    return x[np.random.default_rng(seed).permutation(len(x))].copy()
