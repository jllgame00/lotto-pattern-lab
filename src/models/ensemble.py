"""Cross-sectional normalization and explicitly frozen historical ensembles."""
import json
import numpy as np
from scipy.stats import rankdata
from src.models.predictive import _scores, rank_numbers
from src.research_seal import assert_open


def normalize_scores(scores,method='rank'):
    values=_scores({int(k):v for k,v in scores.items()})
    if method not in ('rank','score'): raise ValueError('Unknown normalization')
    if np.ptp(values)<1e-12: return np.full(45,.5)
    if method=='rank': return (rankdata(values,method='average')-1)/44
    return (values-values.min())/np.ptp(values)


class FrozenEnsemble:
    def __init__(self,components,*,method='rank',weights=None,development_end=None):
        self.components=tuple(components); self.method=method
        if not components or len(set(components))!=len(components) or method not in ('rank','score'):
            raise ValueError('Distinct components and a known normalization required')
        w=np.ones(len(components)) if weights is None else np.asarray(weights,float)
        if w.shape!=(len(components),) or not np.isfinite(w).all() or np.any(w<0) or w.sum()<=0:
            raise ValueError('Finite nonnegative weights required')
        self.weights=w/w.sum(); self.weights.setflags(write=False)
        self.development_end=development_end; self.selection=[]

    def _matrix(self,rows):
        selected=rows[rows.model.isin(self.components)]
        if len(selected)!=len(self.components) or selected.model.nunique()!=len(self.components) or selected.target_draw.nunique()!=1:
            raise ValueError('Exactly one row per component and target required')
        return np.array([normalize_scores(json.loads(selected[selected.model==name].iloc[0].scores),self.method) for name in self.components])

    def select(self,development,*,development_end):
        assert_open(development,'target_draw')
        if self.development_end is not None: raise ValueError('Ensemble weights are already frozen')
        if development.empty or development.target_draw.max()>development_end:
            raise ValueError('Weight selection cannot access later evaluation observations')
        batches=[(self._matrix(group),set(json.loads(group.iloc[0].actual))) for _,group in development.groupby('target_draw')]
        # Small prespecified search: equal weights, or double just one component.
        candidates=[np.ones(len(self.components))]
        candidates += [np.ones(len(self.components))+np.eye(len(self.components))[j] for j in range(len(self.components))]
        for w in candidates:
            w=w/w.sum()
            hits=[len(set((np.argsort(-(w@x),kind='stable')+1)[:6])&actual) for x,actual in batches]
            self.selection.append(dict(weights=w.tolist(),development_avg_hits=float(np.mean(hits))))
        best=max(range(len(candidates)),key=lambda j:self.selection[j]['development_avg_hits'])
        self.weights=np.asarray(self.selection[best]['weights']); self.weights.setflags(write=False)
        self.development_end=int(development_end)
        return self

    def score(self,rows):
        assert_open(rows,'target_draw')
        if self.development_end is None or rows.target_draw.min()<=self.development_end:
            raise ValueError('Ensemble evaluation must strictly follow frozen development cutoff')
        values=self.weights@self._matrix(rows)
        return dict(zip(range(1,46),values.tolist()))

    def configuration(self):
        return dict(components=self.components,normalization=self.method,weights=self.weights.tolist(),
                    development_end=self.development_end,selection=self.selection)
