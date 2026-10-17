"""H18 historical frequency models with exact causal prefix bindings.

Each score recomputes segmentation on the prefix ending immediately before
its target, independently of the comparison engine's outer refit cadence.
These models expose rankings only for historical targets through draw1245.
"""
from functools import lru_cache

import numpy as np

from src.analysis.change_point import segment
from src.analysis.change_point_representation import MINIMUMS, MULTIPLIERS, build_contexts
from src.analysis.recurrence import research_matrix


REPRESENTATIONS = ('A', 'B13', 'B26', 'B52', 'C')
SHRINKAGES = (26, 104)
WINDOWS = (26, 52, 104)


@lru_cache(maxsize=2)
def _contexts(raw, shape):
    """Share expensive prefix costs across all sixty development candidates."""
    x = np.frombuffer(raw, dtype=np.bool_).reshape(shape)
    return build_contexts(x, cutoff=len(x))


@lru_cache(maxsize=30)
def _fits(raw, shape, representation, minimum, multiplier):
    """Shrinkage does not change segmentation, giving thirty fits per prefix."""
    context = _contexts(raw, shape)[representation]
    block = context.get('block_size', 1)
    effective_minimum = ((minimum + block - 1) // block) * block
    penalty = float(multiplier * context['dimension'] * np.log(context['observations']))
    result = segment(context['costs'], context['endpoints'],
                     minimum=effective_minimum, penalty=penalty)[0]
    return dict(result=result, effective_minimum=effective_minimum,
                observations=context['observations'], dimension=context['dimension'],
                segmentation_used_draws=context['used_draws'],
                discarded_tail=context['discarded_tail'], block_size=block)


class _HistoricalPrefix:
    """Bind an immutable fit prefix while allowing causal extension at scoring."""
    def fit(self, x, *, cutoff):
        x = research_matrix(x)
        if type(cutoff) is not int or cutoff != len(x) or cutoff < self._minimum_history:
            raise ValueError(f'Exact training prefix>={self._minimum_history} required')
        self._training_raw = x.tobytes()
        self.training = np.frombuffer(self._training_raw, dtype=np.bool_).reshape(x.shape)
        self.training_cutoff = cutoff
        self.last_state = None
        self.last_diagnostic = []
        return self

    def _current(self, x, target):
        x = research_matrix(x)
        if (not hasattr(self, 'training_cutoff') or type(target) is not int or
                target != len(x) + 1 or target > 1245 or target <= self.training_cutoff or
                x[:self.training_cutoff].tobytes() != self._training_raw):
            raise ValueError('Historical target<=1245 requires unchanged training prefix ending T-1')
        return x

    def _record(self, x, *, representation, boundary, boundaries, shrinkage, **support):
        current = x[boundary:]
        counts = current.sum(axis=0)
        rates = counts / len(current)
        long_term = x.mean(axis=0)
        scores = (counts + shrinkage * long_term) / (len(current) + shrinkage)
        weight = len(current) / (len(current) + shrinkage)
        self.score_training_cutoff = len(x)
        self.last_state = dict(training_cutoff=len(x), representation=representation,
            last_change_point=boundary, segment_length=len(current),
            segment_rates=rates.tolist(), current_rates=scores.tolist(),
            boundaries=list(boundaries), segment_counts=counts.tolist(),
            prefix_rates=long_term.tolist(), shrinkage=shrinkage,
            segment_weight=weight, **support)
        self.last_diagnostic = [dict(number=j+1, training_cutoff=len(x),
            last_change_point=boundary, segment_length=len(current),
            segment_events=int(counts[j]), segment_rate=float(rates[j]),
            prefix_rate=float(long_term[j]), shrinkage=shrinkage,
            segment_weight=weight, score=float(scores[j])) for j in range(45)]
        if not np.isfinite(scores).all():
            raise ValueError('Finite 45-number frequency scores required')
        return dict(enumerate(scores.tolist(), 1))


class RegimeFrequencyModel(_HistoricalPrefix):
    """Shrink the latest fitted segment's rates toward whole-prefix rates.

    A/C boundaries use the declared 13-draw grid. B uses complete blocks for
    segmentation and rounds minimum lengths up to complete blocks. Its current
    predictive segment includes all completed draws after the final boundary,
    including the trailing draws excluded from B's segmentation costs.
    """
    _minimum_history = 104

    def __init__(self, representation='A', minimum=26, multiplier=1, shrinkage=26):
        if (type(representation) is not str or representation not in REPRESENTATIONS or
                type(minimum) is not int or minimum not in MINIMUMS or
                type(multiplier) is not int or multiplier not in MULTIPLIERS or
                type(shrinkage) is not int or shrinkage not in SHRINKAGES):
            raise ValueError('Outside predeclared H18 regime grid')
        self.representation = representation
        self.minimum = minimum
        self.multiplier = multiplier
        self.shrinkage = shrinkage

    def score_matrix(self, x, *, target):
        x = self._current(x, target)
        fit = _fits(x.tobytes(), x.shape, self.representation, self.minimum, self.multiplier)
        result = fit['result']
        boundaries = result['boundaries']
        boundary = int(boundaries[-1]) if boundaries else 0
        support = {key:value for key,value in fit.items() if key != 'result'}
        return self._record(x, representation=self.representation, boundary=boundary,
            boundaries=boundaries, shrinkage=self.shrinkage, minimum=self.minimum,
            multiplier=self.multiplier, penalty=result['penalty'],
            segmentation_gain=result['gain'], segmentation_objective=result['objective'], **support)

    def configuration(self):
        return dict(representation=self.representation, minimum=self.minimum,
                    multiplier=self.multiplier, shrinkage=self.shrinkage)


class AdaptiveWindowBaseline(_HistoricalPrefix):
    """Recompute a declared fixed trailing frequency window at every target."""
    def __init__(self, window=26):
        if type(window) is not int or window not in WINDOWS:
            raise ValueError('Declared fixed window26/52/104 required')
        self.window = window
        self._minimum_history = window

    def score_matrix(self, x, *, target):
        x = self._current(x, target)
        boundary = len(x) - self.window
        return self._record(x, representation=f'Frequency{self.window}', boundary=boundary,
            boundaries=[], shrinkage=0, window=self.window, effective_minimum=self.window,
            segmentation_used_draws=len(x), discarded_tail=0)

    def configuration(self):
        return dict(window=self.window)
