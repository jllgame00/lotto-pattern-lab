"""Nearest historical successors with explicit prefix and raw-support contracts."""
from dataclasses import asdict
import numpy as np
from src.analysis.recurrence import (EmbeddingConfig, research_matrix, observations,
    embed, fit_scaler, distances)


def trajectory_distances(e, ends, config, queries, length=1):
    """Mean aligned state distance, not a distance between unaligned endpoints."""
    offset = int(ends[0])
    candidates = ends[length-1:]
    queries = np.asarray(queries,int)
    if np.any(queries < candidates[0]) or np.any(queries > ends[-1]):
        raise ValueError('Incomplete or future trajectory')
    result = np.zeros((len(queries),len(candidates)))
    for lag in range(length):
        result += distances(e[queries-offset-lag],e[candidates-offset-lag],config.metric)/length
    valid = candidates[None,:]+1 < queries[:,None]-config.span-length+1
    return np.where(valid,result,np.inf), candidates


def successor_scores(x, endpoints, distance, k, weighting, *, neighbor_order=None):
    order = (np.argsort(distance,axis=1,kind='stable') if neighbor_order is None else neighbor_order)[:,:k]
    chosen = np.take_along_axis(distance,order,axis=1)
    if not np.isfinite(chosen).all():
        raise ValueError('Insufficient valid historical analogs')
    weights = np.ones_like(chosen) if weighting == 'uniform' else 1/(chosen+1e-6)
    outcomes = x[endpoints[order]].astype(float)
    return np.einsum('ij,ijk->ik',weights,outcomes)/weights.sum(axis=1)[:,None]


class RecurrenceAnalogModel:
    def __init__(self, config=EmbeddingConfig(), *, k=10, weighting='uniform', length=1):
        if not isinstance(config,EmbeddingConfig) or k not in (1,5,10,20,40) or weighting not in ('uniform','inverse') or length not in (1,2,3):
            raise ValueError('Outside declared analog search')
        self.config, self.k, self.weighting, self.length = config,k,weighting,length

    def fit(self, x, *, cutoff):
        x = research_matrix(x)
        if cutoff != len(x) or cutoff <= self.config.span+self.length:
            raise ValueError('Fit requires exact and sufficient training prefix')
        self.training, self.training_cutoff = x.copy(),cutoff
        o = observations(x,self.config)
        self.scaler = fit_scaler(o,cutoff) if self.config.metric == 'euclidean' else None
        return self

    def _distances(self,x,target):
        x = research_matrix(x)
        if (type(target) is not int or target != len(x)+1 or target > 1245 or
                target <= self.training_cutoff or not np.array_equal(x[:self.training_cutoff],self.training)):
            raise ValueError('Historical prediction requires unchanged training prefix, endpoint T-1 and target<=1245')
        e,ends = embed(observations(x,self.config),self.config,self.scaler)
        d,candidates = trajectory_distances(e,ends,self.config,[target-1],self.length)
        return x,d,candidates

    def score_matrix(self,x,*,target):
        x,d,candidates = self._distances(x,target)
        scores = successor_scores(x,candidates,d,self.k,self.weighting)[0]
        return dict(enumerate(scores.tolist(),1))

    def analogs(self,x,*,target):
        x,d,candidates = self._distances(x,target)
        order = np.argsort(d[0],kind='stable')[:self.k]
        if not np.isfinite(d[0,order]).all(): raise ValueError('Insufficient valid analogs')
        return [dict(endpoint=int(candidates[i]),successor_draw=int(candidates[i]+1),
            successor_numbers=(np.flatnonzero(x[candidates[i]])+1).tolist(),distance=float(d[0,i]),
            **asdict(self.config),length=self.length) for i in order]

    def configuration(self):
        return dict(embedding=asdict(self.config),k=self.k,weighting=self.weighting,length=self.length)


class NearestSuccessorBaseline(RecurrenceAnalogModel):
    def __init__(self,config=EmbeddingConfig()):
        super().__init__(config,k=1)


class RecurrenceContinuationModel(RecurrenceAnalogModel):
    def __init__(self,config=EmbeddingConfig(),*,k=10,weighting='uniform',length=2):
        if length not in (2,3): raise ValueError('Continuation length must be 2 or 3')
        super().__init__(config,k=k,weighting=weighting,length=length)
