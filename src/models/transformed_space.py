"""Causal modular, absolute-distance, and normalized-gap ranking models.

Every score uses the exact completed prefix ending at target-1. Shape and
cross-family models are candidates only; development gates belong to the
backtest selection layer, never to these scoring primitives.
"""
from functools import lru_cache

import numpy as np

from src.analysis.recurrence import research_matrix
from src.analysis.modular_space import representation, transition
from src.analysis.difference_space import (
    absolute_relation, representation as difference_representation,
)


MODULI = (2, 3, 4, 5, 6, 7)
LAGS = (1, 2, 3, 4, 8, 13, 26)
_DISTANCE = np.abs(np.arange(1, 46)[:, None] - np.arange(1, 46)[None, :])


@lru_cache(maxsize=24)
def _modular_context(raw, shape, modulus, lag):
    x = np.frombuffer(raw, dtype=np.bool_).reshape(shape)
    return representation(x, modulus), transition(x, modulus, lag)


@lru_cache(maxsize=14)
def _difference_context(raw, shape, lag):
    x = np.frombuffer(raw, dtype=np.bool_).reshape(shape)
    return absolute_relation(x, lag)


@lru_cache(maxsize=4)
def _shape_context(raw, shape):
    x = np.frombuffer(raw, dtype=np.bool_).reshape(shape)
    return difference_representation(x)


class _Prefix:
    """Shared exact-prefix and immutable fitted-history contract."""

    def fit(self, x, *, cutoff):
        x = research_matrix(x)
        if type(cutoff) is not int or cutoff != len(x) or cutoff < 104:
            raise ValueError('Exact completed prefix with >=104 draws required')
        self.training = x.copy()
        self.training_cutoff = cutoff
        return self

    def score_matrix(self, x, *, target):
        x = research_matrix(x)
        if (not hasattr(self, 'training_cutoff') or type(target) is not int
                or target != len(x) + 1 or target > 1245
                or target <= self.training_cutoff
                or not np.array_equal(x[:self.training_cutoff], self.training)):
            raise ValueError('Historical target<=1245 requires unchanged training prefix ending T-1')
        scores = np.asarray(self._scores(x), dtype=float)
        if scores.shape != (45,) or not np.isfinite(scores).all():
            raise ValueError('Model must return 45 finite number scores')
        return dict(enumerate(scores.tolist(), 1))


class ModularResidueModel(_Prefix):
    """A single modular histogram transition, with 50 prior observations."""

    def __init__(self, modulus=2, lag=1):
        if (type(modulus) is not int or modulus not in MODULI
                or type(lag) is not int or lag not in LAGS):
            raise ValueError('Outside declared modular development grid')
        self.modulus, self.lag = modulus, lag

    def _scores(self, x):
        rep, table = _modular_context(x.tobytes(), x.shape, self.modulus, self.lag)
        source_index = len(x) - self.lag
        state = rep['histogram'][source_index].astype(int)
        residue = np.arange(self.modulus)
        support = table['counts'][residue, state]
        baseline = table['baseline']
        conditional = np.where(
            support >= 20,
            (table['sums'][residue, state] + 50 * baseline) / (support + 50),
            baseline,
        )
        class_score = conditional / rep['populations']
        number_residue = np.arange(1, 46) % self.modulus
        self.last_diagnostic = [dict(
            number=n, k=self.modulus, r=int(r), source_draw=source_index + 1,
            state=int(state[r]), support=int(support[r]),
            conditional=float(conditional[r]), baseline=float(baseline[r]),
            score=float(class_score[r]),
        ) for n, r in enumerate(number_residue, 1)]
        return class_score[number_residue]

    def configuration(self):
        return dict(modulus=self.modulus, lag=self.lag)


class DifferenceRelationModel(_Prefix):
    """Opportunity-adjusted absolute distances with fixed shrinkage 100."""

    def __init__(self, lag=1, support=20):
        if (type(lag) is not int or lag not in LAGS
                or type(support) is not int or support not in (20, 40)):
            raise ValueError('Outside declared distance development grid')
        self.lag, self.support = lag, support

    def _scores(self, x):
        table = _difference_context(x.tobytes(), x.shape, self.lag)
        p = 6 / 45
        observed, opportunity = table['observed'], table['opportunity']
        rates = (observed + 100 * p) / (opportunity + 100)
        weights = np.where(observed >= self.support, rates / p - 1, 0.)
        weights[0] = 0.
        source_index = len(x) - self.lag
        source = np.flatnonzero(x[source_index])
        contributions = weights[_DISTANCE[:, source]]
        boundary = weights[_DISTANCE].mean(axis=1)
        score = contributions.mean(axis=1) - boundary
        self.last_diagnostic = [dict(
            number=n + 1, source_draw=source_index + 1,
            source_numbers=(source + 1).tolist(),
            distances=_DISTANCE[n, source].tolist(),
            weights=contributions[n].tolist(), boundary_term=float(boundary[n]),
            score=float(score[n]),
        ) for n in range(45)]
        return score

    def configuration(self):
        return dict(lag=self.lag, support=self.support)


class GapShapeModel(_Prefix):
    """Stable nearest shapes, at least 26 draws away, smooth actual successors."""

    def __init__(self, K=10, sigma=1):
        if (type(K) is not int or K not in (10, 25)
                or type(sigma) not in (int, float) or sigma not in (1, 2)):
            raise ValueError('Outside declared gap-shape development grid')
        self.K, self.sigma = K, sigma

    def _scores(self, x):
        rep = _shape_context(x.tobytes(), x.shape)
        normalized = rep['normalized_gaps']
        query_index = len(x) - 1
        candidates = np.arange(query_index - 26 + 1)
        distances = np.linalg.norm(normalized[candidates] - normalized[query_index], axis=1)
        chosen = np.argsort(distances, kind='stable')[:self.K]
        neighbors = candidates[chosen]
        # Numeric labels are a bounded axis: normalize each position's kernel
        # inside 1..45 before averaging over all six positions and neighbors.
        successors = np.array([np.flatnonzero(x[j + 1]) + 1 for j in neighbors])
        number = np.arange(1, 46)
        kernels = np.exp(-.5 * ((number - successors[..., None]) / self.sigma) ** 2)
        kernels /= kernels.sum(axis=-1, keepdims=True)
        score = kernels.mean(axis=(0, 1))
        self.last_diagnostic = [dict(
            number=n + 1, query_draw=len(x), neighbor_draws=(neighbors + 1).tolist(),
            successor_draws=(neighbors + 2).tolist(),
            neighbor_distances=distances[chosen].tolist(),
            successor_numbers=successors.tolist(), score=float(score[n]),
        ) for n in range(45)]
        return score

    def configuration(self):
        return dict(K=self.K, sigma=self.sigma)


class ModularDifferenceConsensus(_Prefix):
    """Equal mean inverse permutation ranks; no fitted mixing weights."""

    def __init__(self, modular_model, difference_model):
        if (not isinstance(modular_model, ModularResidueModel)
                or not isinstance(difference_model, DifferenceRelationModel)):
            raise ValueError('One modular parent and one distance parent required')
        self.modular_model, self.difference_model = modular_model, difference_model

    def _scores(self, x):
        ranks = []
        for model in (self.modular_model, self.difference_model):
            order = np.argsort(-model._scores(x), kind='stable')
            rank = np.empty(45, dtype=int)
            rank[order] = np.arange(1, 46)
            ranks.append(rank)
        score = -(ranks[0] + ranks[1]) / 2
        self.last_diagnostic = [dict(
            number=n + 1, modular_rank=int(ranks[0][n]),
            difference_rank=int(ranks[1][n]), score=float(score[n]),
        ) for n in range(45)]
        return score

    def configuration(self):
        return dict(modular=self.modular_model.configuration(),
                    difference=self.difference_model.configuration())
