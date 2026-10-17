"""Training-only binary information heuristics with an auditable causal prefix.

Positive Miller--Madow information weights supported conditional forecasts. The
support filters are training heuristics, not statistical significance tests.
Scores are bounded conditional estimates, with no lottery calibration claim.
"""
from functools import lru_cache

import numpy as np

from src.analysis.information import LAGS, HISTORIES, mi_matrix, te_matrix
from src.analysis.recurrence import research_matrix

WINDOW = 624
CONTEXT_SUPPORT = 20
SHRINKAGE = 20.


@lru_cache(maxsize=7)
def _mi_matrix_cache(raw, shape, lag):
    """Share one training table between incoming counts of 3 and 5."""
    return mi_matrix(np.frombuffer(raw, dtype=np.bool_).reshape(shape), lag)


@lru_cache(maxsize=28)
def _te_matrix_cache(raw, shape, lag, k, l):
    return te_matrix(np.frombuffer(raw, dtype=np.bool_).reshape(shape), lag, k, l)


def _validate(lag, k=1, l=1, incoming=3):
    if (type(lag) is not int or lag not in LAGS or type(k) is not int or
            type(l) is not int or (k, l) not in HISTORIES or
            type(incoming) is not int or incoming not in (3, 5)):
        raise ValueError('Outside declared information model search')


def _state(x, depth, offset):
    """Most recent history bit is the least significant bit."""
    return sum((1 << r) * x[-offset-r].astype(int) for r in range(depth))


def _choose(table, target, support, incoming):
    weights = np.asarray(table['corrected'])[:, target]
    eligible = (np.asarray(table['eligible'])[:, target] & np.isfinite(weights) &
                (weights > 0) & (support >= CONTEXT_SUPPORT))
    eligible[target] = False
    sources = np.flatnonzero(eligible)
    return sorted(sources.tolist(), key=lambda i: (-weights[i], i))[:incoming]


class _PrefixModel:
    def fit(self, x, *, cutoff):
        x = research_matrix(x)
        if type(cutoff) is not int or cutoff != len(x) or cutoff < 300:
            raise ValueError('Exact training prefix of at least 300 draws required')
        self.training = x.copy()
        self.training_cutoff = cutoff
        return self

    def score_matrix(self, x, *, target):
        x = research_matrix(x)
        if (not hasattr(self, 'training_cutoff') or type(target) is not int or
                target != len(x) + 1 or target > 1245 or
                target <= self.training_cutoff or
                not np.array_equal(x[:self.training_cutoff], self.training)):
            raise ValueError('Historical target<=1245 requires unchanged prefix ending T-1')
        scores = self._scores(x[-WINDOW:])
        return dict(enumerate(np.clip(scores, 1e-6, 1 - 1e-6).tolist(), 1))


class MutualInformationModel(_PrefixModel):
    def __init__(self, lag=1, incoming=3):
        _validate(lag, incoming=incoming)
        self.lag, self.incoming = lag, incoming

    def _scores(self, x):
        table = _mi_matrix_cache(x.tobytes(), x.shape, self.lag)
        counts = table['counts']
        base = x[self.lag:].mean(axis=0)
        current = _state(x, 1, self.lag)
        scores = base.copy()
        self.last_diagnostic = []
        for j in range(45):
            cells = counts[np.arange(45), j, current]
            support = cells.sum(axis=-1)
            chosen = _choose(table, j, support, self.incoming)
            total = sum(float(table['corrected'][i, j]) for i in chosen)
            edges = []
            for i in chosen:
                conditional = (cells[i, 1] + SHRINKAGE * base[j]) / (support[i] + SHRINKAGE)
                weight = float(table['corrected'][i, j]) / total
                edges.append(dict(source=i+1, information=float(table['corrected'][i, j]),
                                  context_support=int(support[i]), conditional=float(conditional),
                                  weight=weight))
            if edges:
                scores[j] = sum(edge['weight'] * edge['conditional'] for edge in edges)
            self.last_diagnostic.append(dict(number=j+1, baseline=float(base[j]), selected=edges))
        return scores

    def configuration(self):
        return dict(lag=self.lag, incoming=self.incoming)


class TargetHistoryBaseline(_PrefixModel):
    """TE-aligned own-history ablation, including the same shrinkage prior."""
    def __init__(self, lag=1, k=1, l=1):
        _validate(lag, k, l)
        self.lag, self.k, self.l = lag, k, l

    def _context(self, x):
        table = _te_matrix_cache(x.tobytes(), x.shape, self.lag, self.k, self.l)
        start = max(self.lag + self.l - 1, self.k)
        overall = x[start:].mean(axis=0)
        current = _state(x, self.k, 1)
        own = table['past_future_counts'][np.arange(45), current]
        baseline = (own[:, 1] + SHRINKAGE * overall) / (own.sum(axis=-1) + SHRINKAGE)
        return table, current, baseline

    def _scores(self, x):
        _, _, baseline = self._context(x)
        self.last_diagnostic = [dict(number=j+1, baseline=float(baseline[j]), selected=[])
                                for j in range(45)]
        return baseline

    def configuration(self):
        return dict(lag=self.lag, k=self.k, l=self.l)


class TransferEntropyModel(TargetHistoryBaseline):
    def __init__(self, lag=1, k=1, l=1, incoming=3):
        _validate(lag, k, l, incoming)
        super().__init__(lag, k, l)
        self.incoming = incoming

    def _scores(self, x):
        table, target_past, baseline = self._context(x)
        source_past = _state(x, self.l, self.lag)
        scores = baseline.copy()
        self.last_diagnostic = []
        for j in range(45):
            cells = table['counts'][np.arange(45), j, source_past, target_past[j]]
            support = cells.sum(axis=-1)
            chosen = _choose(table, j, support, self.incoming)
            total = sum(float(table['corrected'][i, j]) for i in chosen)
            edges = []
            for i in chosen:
                conditional = (cells[i, 1] + SHRINKAGE * baseline[j]) / (support[i] + SHRINKAGE)
                weight = float(table['corrected'][i, j]) / total
                edges.append(dict(source=i+1, information=float(table['corrected'][i, j]),
                                  context_support=int(support[i]), conditional=float(conditional),
                                  weight=weight))
            scores[j] += sum(edge['weight'] * (edge['conditional'] - baseline[j]) for edge in edges)
            self.last_diagnostic.append(dict(number=j+1, baseline=float(baseline[j]), selected=edges))
        return scores

    def configuration(self):
        return dict(lag=self.lag, k=self.k, l=self.l, incoming=self.incoming)
