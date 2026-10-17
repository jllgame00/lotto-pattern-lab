"""Historical, prefix-frozen renewal and discrete event influence models.

These are per-number Bernoulli pseudo-likelihoods, not joint draw models.
Selection, centering, baselines and coefficients are fitted once at the outer
cutoff. Only strictly earlier event states change between subsequent targets.
"""
from copy import deepcopy
from functools import lru_cache

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit

from src.analysis.point_process import (LAGS, SCHEMES, KERNELS, all_effects,
    current_renewal_state, renewal_table)
from src.analysis.recurrence import research_matrix


def _readonly(values):
    values = np.asarray(values)
    return np.frombuffer(values.tobytes(), dtype=values.dtype).reshape(values.shape)


class _HistoricalPrefix:
    def _bind(self, x, cutoff):
        x = research_matrix(x)
        if type(cutoff) is not int or cutoff != len(x) or cutoff < 300:
            raise ValueError('Exact training prefix>=300 required')
        self._training_raw = x.tobytes()
        self.training = np.frombuffer(self._training_raw, dtype=np.bool_).reshape(x.shape)
        self.training_cutoff = cutoff
        self.last_diagnostic = []
        return self.training

    def _current(self, x, target):
        x = research_matrix(x)
        if (not hasattr(self, 'training_cutoff') or type(target) is not int or
                target != len(x)+1 or target > 1245 or target <= self.training_cutoff or
                x[:self.training_cutoff].tobytes() != self._training_raw):
            raise ValueError('Historical target<=1245 requires unchanged training prefix ending T-1')
        return x


class RenewalModel(_HistoricalPrefix):
    def __init__(self, scheme='coarse', alpha=26):
        if type(scheme) is not str or scheme not in SCHEMES or type(alpha) is not int or alpha not in (26, 104):
            raise ValueError('Outside declared renewal grid')
        self.scheme, self.alpha = scheme, alpha

    def fit(self, x, *, cutoff):
        x = self._bind(x, cutoff)
        self.table = {key: _readonly(value) if isinstance(value, np.ndarray) else value
                      for key, value in renewal_table(x, self.scheme, alpha=self.alpha, minimum=20).items()}
        self.baseline = self.table['baseline']
        return self

    def score_matrix(self, x, *, target):
        x = self._current(x, target)
        states = current_renewal_state(x, self.scheme)
        scores = self.baseline.copy()
        diagnostics = []
        for j, state in enumerate(states):
            state = int(state)
            valid = 0 <= state < self.table['support'].shape[1]
            support = int(self.table['support'][j, state]) if valid else 0
            if valid and support >= 20:
                scores[j] = self.table['conditional'][j, state]
            diagnostics.append(dict(number=j+1, state=state, support=support,
                baseline=float(self.baseline[j]), probability=float(scores[j]), score=float(scores[j]),
                fallback=not valid or support < 20, source_cutoff=len(x), training_cutoff=self.training_cutoff))
        self.last_diagnostic = diagnostics
        self.score_training_cutoff = self.training_cutoff
        return dict(enumerate(scores.tolist(), 1))

    def configuration(self):
        return dict(scheme=self.scheme, alpha=self.alpha)


def _kernel_weights(kernel):
    if kernel == 'finite':
        return np.full(len(LAGS), 1/len(LAGS))
    tau = 2 if kernel == 'exp2' else 8
    weights = np.exp(-(np.asarray(LAGS)-1)/tau)
    return weights / weights.sum()


def _select_edges(x, kernel, incoming, alpha, signed):
    """Project all supported lag effects before choosing incoming source numbers.

    Finite signed edges carry direction in each lag weight; exponential signed
    edges carry direction in their amplitude. Strength ranks source candidates;
    bounded log-odds amplitudes control their contribution to the convolution.
    """
    effects = all_effects(x, alpha=alpha, minimum=30)
    fixed_weights = _kernel_weights(kernel)
    selected = []
    for j in range(45):
        candidates = []
        for i in range(45):
            if i == j:
                continue
            support = effects['support'][:, i, j]
            eligible = effects['eligible'][:, i, j] & (support >= 30)
            # A kernel uses the complete declared lag profile. A source must
            # support every lag before any of its events enter forecasting.
            if not np.all(eligible):
                continue
            delta = np.where(eligible, effects['effect'][:, i, j], 0.)
            odds = np.where(eligible, effects['log_odds'][:, i, j], 0.)
            if not signed:
                delta = np.maximum(delta, 0.)
                odds = np.maximum(odds, 0.)
            if kernel == 'finite':
                strength = float(np.abs(delta).sum())
                if strength <= 0:
                    continue
                weights = delta / strength
                magnitude = float(np.dot(np.abs(weights), np.abs(odds)))
                amplitude = float(min(1., magnitude))
            else:
                strength = float(np.dot(fixed_weights, np.abs(delta) if signed else delta))
                projected_odds = float(np.dot(fixed_weights, odds))
                if strength <= 0:
                    continue
                weights = fixed_weights
                amplitude = float(np.clip(projected_odds, -1. if signed else 0., 1.))
            active = eligible & (np.abs(delta) > 0)
            if amplitude == 0 or not active.any():
                continue
            candidates.append(dict(source=i+1, target=j+1, strength=abs(strength),
                raw_effect=float(np.dot(fixed_weights, delta)) if kernel != 'finite' else float(delta.sum()),
                amplitude=amplitude, support=int(np.min(support)),
                lag_support=support.astype(int).tolist(), lag_weights=weights.tolist(),
                lag_effects=delta.tolist(), training_cutoff=len(x)))
        candidates.sort(key=lambda edge: (-edge['strength'], edge['source']))
        edges = candidates[:incoming]
        normalization = max(1., sum(abs(edge['amplitude']) for edge in edges))
        for edge in edges:
            edge['amplitude'] /= normalization
        selected.append(edges)
    return selected


def _raw_features(x, outcomes, self_weights, edges):
    """At outcome index t, every feature reads x[t-lag], with lag>=1."""
    indices = np.asarray(outcomes, dtype=int)
    events = np.stack([x[indices-int(lag)] for lag in LAGS], axis=1).astype(float)
    features = np.zeros((len(indices), 45, 2))
    features[:, :, 0] = np.einsum('tlj,l->tj', events, self_weights)
    for j, incoming in enumerate(edges):
        for edge in incoming:
            features[:, j, 1] += (events[:, :, edge['source']-1] @ np.asarray(edge['lag_weights'])
                                  * edge['amplitude'] / len(incoming))
    return features


@lru_cache(maxsize=24)
def _prepared_training(raw, shape, kernel, incoming, alpha, signed):
    """Ridge-independent frozen features shared by the two ridge candidates."""
    x = np.frombuffer(raw, dtype=np.bool_).reshape(shape)
    edges = _select_edges(x, kernel, incoming, alpha, signed)
    weights = _kernel_weights(kernel)
    indices = np.arange(max(max(LAGS), len(x)-416), len(x))
    baseline = (x.sum(axis=0)+2)/(len(x)+15)
    raw_features = _raw_features(x, indices, weights, edges)
    for incoming_edges in edges:
        for edge in incoming_edges:
            events = x[indices[:, None]-np.asarray(LAGS), edge['source']-1]
            edge['training_mean'] = float(np.mean(events @ np.asarray(edge['lag_weights']))
                                          * edge['amplitude']/len(incoming_edges))
    means = raw_features.mean(axis=0)
    scales = np.broadcast_to(np.maximum(np.sqrt(baseline*(1-baseline)), .05)[:, None], (45, 2)).copy()
    features = np.clip((raw_features-means)/scales, -3, 3)
    return dict(edges=edges, self_weights=_readonly(weights), baseline=_readonly(baseline),
        means=_readonly(means), scales=_readonly(scales),
        features=_readonly(features.reshape(-1, 2)), outcomes=_readonly(x[indices].astype(float).ravel()),
        offsets=_readonly(np.broadcast_to(logit(baseline), (len(indices), 45)).ravel()),
        indices=_readonly(indices))


def _ridge_objective(beta, features, outcomes, offsets, ridge):
    """SUM Bernoulli negative log-likelihood with analytic ridge gradient."""
    logits = offsets + features @ beta
    value = np.sum(np.logaddexp(0, logits)-outcomes*logits) + .5*ridge*np.dot(beta, beta)
    gradient = features.T @ (expit(logits)-outcomes) + ridge*beta
    return float(value), gradient


def _bounded_fit(features, outcomes, offsets, ridge, bounds):
    """Solve the unchanged SUM objective with checked box-constrained KKT.

    Scale the whole objective, including its ridge term, for line search: at
    SUM loss near7300, an otherwise valid Newton step can improve less than
    one floating-point ULP and make unscaled L-BFGS-B report ABNORMAL.
    """
    rows = len(outcomes)
    args = features, outcomes, offsets, ridge
    baseline = _ridge_objective(np.zeros(features.shape[1]), *args)[0]
    def scaled(beta):
        value, gradient = _ridge_objective(beta, *args)
        return value/rows, gradient/rows
    attempts = []
    start = np.zeros(features.shape[1])
    for method, objective, options in (
            ('L-BFGS-B', scaled, dict(ftol=1e-15, gtol=1e-10, maxiter=200, maxls=100)),
            ('SLSQP', lambda beta: _ridge_objective(beta, *args), dict(ftol=1e-12, maxiter=500))):
        result = minimize(objective, start, jac=True, method=method, bounds=bounds, options=options)
        value, gradient = _ridge_objective(result.x, *args)
        projected = gradient.copy()
        feasible = True
        for i, (low, high) in enumerate(bounds):
            feasible &= low-1e-9 <= result.x[i] <= high+1e-9
            if low == high or (result.x[i] <= low+1e-9 and gradient[i] > 0) or (
                    result.x[i] >= high-1e-9 and gradient[i] < 0):
                projected[i] = 0.
        kkt = float(np.max(np.abs(projected)))
        finite = np.isfinite(value) and np.isfinite(result.x).all() and np.isfinite(gradient).all()
        accepted = bool(result.success and feasible and finite and kkt/rows <= 1e-8
                        and value <= baseline+1e-9)
        attempts.append(dict(method=method, success=bool(result.success), accepted=accepted,
            message=str(result.message), objective=float(value), projected_kkt=kkt,
            projected_kkt_per_row=kkt/rows, iterations=int(result.nit)))
        if accepted:
            result.fun, result.jac = value, gradient
            return result, dict(method=method, objective_scale=rows,
                projected_kkt=kkt, projected_kkt_per_row=kkt/rows,
                kkt_per_row_tolerance=1e-8, attempts=attempts)
        if np.isfinite(result.x).all():
            start = np.array([np.clip(v, low, high) for v, (low, high) in zip(result.x, bounds)])
    raise RuntimeError(f'Influence optimization failed checked KKT/objective validation: {attempts}')


class HawkesInfluenceModel(_HistoricalPrefix):
    """Excitation-only pooled logistic regression on frozen event kernels."""
    signed = False

    def __init__(self, kernel='exp2', incoming=1, alpha=26, ridge=1):
        if (type(kernel) is not str or kernel not in KERNELS or type(incoming) is not int or incoming not in (1, 3)
                or type(alpha) is not int or alpha not in (26, 104) or type(ridge) is not int or ridge not in (1, 10)):
            raise ValueError('Outside declared influence grid')
        self.kernel, self.incoming, self.alpha, self.ridge = kernel, incoming, alpha, ridge

    def fit(self, x, *, cutoff):
        x = self._bind(x, cutoff)
        prepared = _prepared_training(self._training_raw, x.shape, self.kernel, self.incoming, self.alpha, self.signed)
        self.selected_edges = deepcopy(prepared['edges'])
        self.self_weights = prepared['self_weights']
        self.baseline = prepared['baseline']
        self.feature_means, self.feature_scales = prepared['means'], prepared['scales']
        self.training_features = prepared['features']
        self.training_outcomes, self.training_offsets = prepared['outcomes'], prepared['offsets']
        self.training_outcome_indices = prepared['indices']
        bounds = [(-3. if self.signed else 0., 3.), (0., 3.)]
        if not any(self.selected_edges):
            bounds[1] = (0., 0.)
        args = (self.training_features, self.training_outcomes, self.training_offsets, self.ridge)
        result, solver = _bounded_fit(*args, bounds)
        self_result, self_solver = _bounded_fit(self.training_features[:, :1], self.training_outcomes,
                                              self.training_offsets, self.ridge, bounds[:1])
        self.coefficients = _readonly(result.x)
        self.self_coefficient = float(self_result.x[0])
        self.optimization_diagnostics = dict(success=bool(result.success), message=str(result.message),
            objective=float(result.fun), baseline_objective=_ridge_objective(np.zeros(2), *args)[0],
            **solver, self_solver=self_solver,
            iterations=int(result.nit), self_success=bool(self_result.success),
            self_objective=float(self_result.fun), self_iterations=int(self_result.nit),
            outcome_start=int(prepared['indices'][0])+1, outcome_end=cutoff,
            outcome_draws=len(prepared['indices']), rows=len(self.training_outcomes))
        return self

    def _features(self, x):
        raw = _raw_features(x, [len(x)], self.self_weights, self.selected_edges)[0]
        self.last_features = np.clip((raw-self.feature_means)/self.feature_scales, -3, 3)
        return raw, self.last_features

    def score_matrix(self, x, *, target):
        x = self._current(x, target)
        raw, features = self._features(x)
        scores = np.clip(expit(logit(self.baseline)+features@self.coefficients), 1e-6, 1-1e-6)
        diagnostics = []
        for j, edges in enumerate(self.selected_edges):
            incoming = []
            unbounded_cross = (raw[j, 1]-self.feature_means[j, 1])/self.feature_scales[j, 1]
            clipping_factor = features[j, 1]/unbounded_cross if unbounded_cross else 1.
            for edge in edges:
                state = float(np.dot(x[len(x)-np.asarray(LAGS), edge['source']-1], edge['lag_weights']))
                raw_contribution = state*edge['amplitude']/len(edges)
                contribution = float((raw_contribution-edge['training_mean'])/self.feature_scales[j, 1]
                                     * clipping_factor*self.coefficients[1])
                incoming.append(dict(edge, state=state, raw_contribution=raw_contribution, contribution=contribution))
            diagnostics.append(dict(number=j+1, baseline=float(self.baseline[j]), self_state=float(raw[j, 0]),
                self_feature=float(features[j, 0]), self_contribution=float(features[j, 0]*self.coefficients[0]),
                cross_state=float(raw[j, 1]), cross_feature=float(features[j, 1]),
                cross_contribution=float(features[j, 1]*self.coefficients[1]), incoming=incoming,
                probability=float(scores[j]), score=float(scores[j]), training_cutoff=self.training_cutoff,
                source_cutoff=len(x)))
        self.last_diagnostic = diagnostics
        self.score_training_cutoff = self.training_cutoff
        return dict(enumerate(scores.tolist(), 1))

    def self_only_scores(self, x, *, target):
        x = self._current(x, target)
        _, features = self._features(x)
        scores = np.clip(expit(logit(self.baseline)+features[:, 0]*self.self_coefficient), 1e-6, 1-1e-6)
        return dict(enumerate(scores.tolist(), 1))

    def configuration(self):
        return dict(kernel=self.kernel, incoming=self.incoming, alpha=self.alpha, ridge=self.ridge,
                    signed=self.signed)

    @staticmethod
    def feature_definition():
        return dict(lags=list(LAGS), finite_self='uniform over seven declared lags',
            self='normalized exponential convolution, or uniform finite convolution',
            cross='mean selected incoming amplitude-weighted convolutions, excludes own number',
            centering='per-number feature mean over fitted last416 outcomes, t>=26',
            scaling='sqrt(fitted per-number baseline*(1-baseline)), floor0.05',
            clipping=[-3, 3], fitting='SUM Bernoulli NLL + 0.5*ridge*sum(beta**2)',
            edge_normalization='each absolute amplitude<=1; total absolute incoming amplitude<=1',
            current='events at T-lag, strictly before target; no edge/scaler/coefficient refit')


class SignedInfluenceModel(HawkesInfluenceModel):
    """Separate signed event family; self beta may inhibit, cross beta>=0."""
    signed = True
