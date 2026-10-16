"""Fitted ranking models with explicit chronological contracts.

The public fit/score_rows interface consumes the shared features. These models
are separate from the stateless ticket interface used by the original engine.
"""
from __future__ import annotations

import importlib.util
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.spatial.distance import cdist

from src.analysis.features import feature_columns


def _scores(scores):
    if set(scores) != set(range(1,46)):
        raise ValueError('Scores must contain exactly numbers 1 through 45')
    values = np.array([scores[n] for n in range(1,46)],dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('All scores must be finite')
    return values


def rank_numbers(scores):
    values = _scores(scores)
    # Deterministic ties: smaller number first. Equal scores are not evidence.
    return (np.argsort(-values,kind='stable')+1).tolist()


def weighted_ticket(scores, *, seed=42):
    weights = _scores(scores)
    if (weights < 0).any():
        raise ValueError('Weighted tickets require nonnegative scores')
    # Tiny uniform mixture permits six unique draws even with sparse scores.
    weights = weights/weights.max() if weights.max() else np.ones(45)
    weights = .999*weights/weights.sum()+.001/45
    return sorted(np.random.default_rng(seed).choice(np.arange(1,46),6,replace=False,p=weights).tolist())


class TrainingTransform:
    """Training medians + population z-scores, fixed number one-hot vocabulary.

    Entirely missing training columns receive zero. Missingness is not fitted
    from current rows. Number identity is categorical, never an ordinal scale.
    """
    def __init__(self, columns):
        self.columns = list(columns)
        allowed = set(feature_columns())
        if not self.columns or len(set(self.columns)) != len(self.columns) or not set(self.columns)<=allowed:
            raise ValueError('Feature subset must contain distinct canonical predictor columns')
        self.numeric = [c for c in self.columns if c!='number']

    def fit(self, rows):
        x = rows[self.numeric].to_numpy(dtype=float,copy=True)
        x[~np.isfinite(x)] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            self.medians = np.nanmedian(x,axis=0)
        self.medians = np.nan_to_num(self.medians)
        x = np.where(np.isnan(x),self.medians,x)
        self.means = x.mean(axis=0)
        self.scales = x.std(axis=0)
        self.scales[self.scales < 1e-12] = 1
        self.names = self.numeric + ([f'number_{n}' for n in range(1,46)] if 'number' in self.columns else [])
        return self

    def transform(self, rows):
        x = rows[self.numeric].to_numpy(dtype=float)
        x = np.where(np.isfinite(x),x,self.medians)
        x = (x-self.means)/self.scales
        if 'number' in self.columns:
            x = np.column_stack([x, rows.number.to_numpy()[:,None]==np.arange(1,46)])
        return x


class FittedModel:
    def __init__(self, *, columns=None, seed=42):
        self.columns = feature_columns() if columns is None else list(columns)
        TrainingTransform(self.columns)  # validate immediately
        self.seed = seed

    def _training(self, rows, cutoff):
        if rows.empty or rows.target_draw.max() > cutoff:
            raise ValueError('Training rows must be nonempty and at or before training cutoff')
        if not rows.feature_cutoff.eq(rows.target_draw-1).all():
            raise ValueError('Feature cutoff must be immediately before target')
        if rows.duplicated(['target_draw','number']).any() or not rows.appeared_next.isin([0,1]).all():
            raise ValueError('Training requires unique rows and observed binary labels')
        self.training_cutoff = int(cutoff)
        self.training_rows = len(rows)
        self.transformer = TrainingTransform(self.columns).fit(rows)
        return self.transformer.transform(rows), rows.appeared_next.to_numpy(dtype=float)

    def _current(self, rows):
        if 'appeared_next' in rows.columns:
            raise ValueError('Scoring rows must not expose target outcomes')
        if len(rows)!=45 or set(rows.number)!=set(range(1,46)) or rows.target_draw.nunique()!=1:
            raise ValueError('Scoring requires one target and exactly 45 numbers')
        if rows.target_draw.min() <= self.training_cutoff or not rows.feature_cutoff.eq(rows.target_draw-1).all():
            raise ValueError('Scoring target must follow training cutoff with causal features')
        return self.transformer.transform(rows)

    def configuration(self):
        return dict(model=type(self).__name__,seed=self.seed,features=self.columns)

    def importance(self):
        return []


class LogisticModel(FittedModel):
    """Pooled regularized logistic regression fitted with SciPy L-BFGS.

    Minimize mean log-loss + ||w||²/(2*C*n), with an unpenalized intercept.
    This is an explicit dependency-light backend, not a different classifier.
    """
    def __init__(self, *, C=1., **kwargs):
        super().__init__(**kwargs)
        if C<=0: raise ValueError('C must be positive')
        self.C = C

    def fit(self, rows, *, cutoff):
        x,y = self._training(rows,cutoff)
        if len(np.unique(y))<2:
            raise ValueError('Logistic regression needs both observed classes')
        penalty = 1/(self.C*len(y))
        def objective(beta):
            z = x@beta[:-1]+beta[-1]
            residual = expit(z)-y
            loss = np.mean(np.logaddexp(0,z)-y*z)+penalty*np.dot(beta[:-1],beta[:-1])/2
            gradient = np.r_[x.T@residual/len(y)+penalty*beta[:-1],residual.mean()]
            return loss,gradient
        initial = np.zeros(x.shape[1]+1)
        initial[-1] = np.log(y.mean()/(1-y.mean()))
        result = minimize(objective,initial,jac=True,method='L-BFGS-B',
                          options=dict(maxiter=500,gtol=1e-7,ftol=1e-11))
        if not result.success:
            raise RuntimeError(f'Logistic optimization failed: {result.message}')
        self.coef = result.x
        self.intercept_probability = float(expit(self.coef[-1]))
        return self

    def score_rows(self, rows):
        x = self._current(rows)
        return dict(zip(rows.number.astype(int),expit(x@self.coef[:-1]+self.coef[-1]).tolist()))

    def importance(self):
        return [dict(feature=name,importance=float(value),kind='standardized_coefficient')
                for name,value in zip(self.transformer.names,self.coef[:-1])]

    def configuration(self):
        return dict(super().configuration(),C=self.C,backend='scipy_l_bfgs_b')


class SimilarityModel(FittedModel):
    def __init__(self, *, k=30, metric='euclidean', weighting='distance', **kwargs):
        super().__init__(**kwargs)
        if not isinstance(k,int) or k<1 or metric not in ('euclidean','cityblock') or weighting not in ('distance','uniform'):
            raise ValueError('Invalid similarity configuration')
        self.k,self.metric,self.weighting = k,metric,weighting

    def fit(self, rows, *, cutoff):
        self._training(rows,cutoff)
        self.states = {}
        for number, group in rows.groupby('number',sort=True):
            group = group.sort_values('target_draw').reset_index(drop=True).copy()
            scaler = TrainingTransform(self.columns).fit(group)
            self.states[int(number)] = (group,scaler,scaler.transform(group))
        if set(self.states)!=set(range(1,46)):
            raise ValueError('Similarity requires training states for all 45 numbers')
        return self

    def explain(self, rows, number):
        self._current(rows)
        if number not in self.states: raise ValueError('Number must be 1..45')
        group,scaler,x = self.states[number]
        current = rows[rows.number==number]
        distances = cdist(scaler.transform(current),x,metric=self.metric)[0]
        indices = np.argsort(distances,kind='stable')[:self.k]
        weights = 1/(1+distances[indices]) if self.weighting=='distance' else np.ones(len(indices))
        # Normalize weights to K observations before adding fixed Beta smoothing.
        weights *= len(indices)/weights.sum()
        outcomes = group.iloc[indices].appeared_next.to_numpy()
        score = float((weights@outcomes+2)/(weights.sum()+15))
        neighbors = [dict(number=number,target_draw=int(group.iloc[i].target_draw),
                          state_cutoff=int(group.iloc[i].feature_cutoff),
                          target_date=str(group.iloc[i].target_date),distance=float(distances[i]),
                          next_appeared=int(group.iloc[i].appeared_next)) for i in indices]
        state = {c:(float(current.iloc[0][c]) if pd.notna(current.iloc[0][c]) else None) for c in self.columns}
        return dict(number=number,current_state=state,neighbors=neighbors,score=score,
                    training_cutoff=self.training_cutoff)

    def score_rows(self, rows):
        self._current(rows)
        scores = {}
        for number in range(1,46):
            group,scaler,x = self.states[number]
            distances = cdist(scaler.transform(rows[rows.number==number]),x,metric=self.metric)[0]
            indices = np.argsort(distances,kind='stable')[:self.k]
            weights = 1/(1+distances[indices]) if self.weighting=='distance' else np.ones(len(indices))
            weights *= len(indices)/weights.sum()
            outcomes = group.appeared_next.to_numpy()[indices]
            scores[number] = float((weights@outcomes+2)/(weights.sum()+15))
        return scores

    def configuration(self):
        return dict(super().configuration(),k=self.k,metric=self.metric,weighting=self.weighting,
                    prior_appearances=2,prior_observations=15)


class ForestModel(FittedModel):
    def fit(self, rows, *, cutoff):
        try:
            from sklearn.ensemble import RandomForestClassifier
        except ImportError as exc:
            raise RuntimeError('RandomForest unavailable: install scikit-learn') from exc
        x,y = self._training(rows,cutoff)
        self.estimator = RandomForestClassifier(n_estimators=100,max_depth=4,min_samples_leaf=50,
                                                max_features='sqrt',random_state=self.seed,n_jobs=1)
        self.estimator.fit(x,y)
        return self

    def score_rows(self, rows):
        x = self._current(rows)
        classes = self.estimator.classes_.tolist()
        values = self.estimator.predict_proba(x)[:,classes.index(1)] if 1 in classes else np.zeros(len(x))
        return dict(zip(rows.number.astype(int),values.tolist()))

    def importance(self):
        return [dict(feature=name,importance=float(value),kind='tree_importance')
                for name,value in zip(self.transformer.names,self.estimator.feature_importances_)]

    def configuration(self):
        return dict(super().configuration(),parameters=self.estimator.get_params())


class BoostingModel(ForestModel):
    def fit(self, rows, *, cutoff):
        if importlib.util.find_spec('lightgbm'):
            from lightgbm import LGBMClassifier
            self.estimator = LGBMClassifier(n_estimators=100,learning_rate=.03,num_leaves=7,max_depth=3,
                                           min_child_samples=100,reg_lambda=1.,random_state=self.seed,
                                           n_jobs=1,deterministic=True,force_col_wise=True,verbosity=-1)
        elif importlib.util.find_spec('xgboost'):
            from xgboost import XGBClassifier
            self.estimator = XGBClassifier(n_estimators=100,learning_rate=.03,max_depth=3,min_child_weight=15,
                                          reg_lambda=1.,random_state=self.seed,n_jobs=1,tree_method='hist')
        else:
            raise RuntimeError('Boosting unavailable: install lightgbm or xgboost; no substitute used')
        x,y = self._training(rows,cutoff)
        self.estimator.fit(x,y)
        return self
