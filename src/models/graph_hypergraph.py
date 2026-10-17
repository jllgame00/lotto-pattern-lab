"""H12 prefix-only relational models. Frequency is explicitly projected out."""
from functools import lru_cache
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.graph_structure import WINDOWS,graph,relational_features,standardize
from src.analysis.hypergraph_structure import continuation_scores
from src.analysis.graph_hypergraph_search import unit_residual


@lru_cache(maxsize=3)
def _graph_context(raw,shape,window):
    x=np.frombuffer(raw,dtype=np.bool_).reshape(shape);g=graph(x,window=window)
    return g,{k:relational_features(g,x[-1],communities=k) for k in (2,3)}


@lru_cache(maxsize=12)
def _hyper_context(raw,shape,window,support,shrinkage):
    x=np.frombuffer(raw,dtype=np.bool_).reshape(shape)
    return continuation_scores(x,window=window,support=support,shrinkage=shrinkage)


class _PrefixModel:
    def fit(self,x,*,cutoff):
        x=research_matrix(x)
        if type(cutoff) is not int or cutoff!=len(x) or cutoff<104:raise ValueError('Exact completed prefix with >=104 draws required')
        self.training=x.copy();self.training_cutoff=cutoff
        return self

    def score_matrix(self,x,*,target):
        x=research_matrix(x)
        if (not hasattr(self,'training_cutoff') or type(target) is not int or target!=len(x)+1 or target>1245 or
            target<=self.training_cutoff or not np.array_equal(x[:self.training_cutoff],self.training)):
            raise ValueError('Historical target<=1245 requires unchanged training prefix endingT-1')
        return dict(enumerate(self._scores(x).tolist(),1))


class RollingFrequencyControl(_PrefixModel):
    """Exact own-frequency comparator on the Phase14 window grid."""
    def __init__(self,window=26):
        if type(window) is not int or window not in WINDOWS:raise ValueError('Declared control window required')
        self.window=window

    def _scores(self,x):return x[-self.window:].mean(0)

    def configuration(self):return dict(window=self.window,score='completed-window appearance frequency')


class GraphStructureModel(_PrefixModel):
    def __init__(self,window=52,feature='neighbor',communities=2):
        if (type(window) is not int or window not in WINDOWS or feature not in ('neighbor','clustering','community','neighbor_community') or
            type(communities) is not int or communities not in (2,3) or (feature in ('neighbor','clustering') and communities!=2)):
            raise ValueError('Outside declared graph development grid')
        self.window,self.feature,self.communities=window,feature,communities

    def _scores(self,x):
        g,features=_graph_context(x.tobytes(),x.shape,self.window);f=features[self.communities]
        score=standardize((f['neighbor']+f['community'])/2) if self.feature=='neighbor_community' else f[self.feature].copy()
        self.last_diagnostic=[dict(number=n+1,window=self.window,own_frequency=int(g['frequency'][n]),
            strength=int(g['strength'][n]),community=int(f['labels'][n]),feature=self.feature,
            raw_features={name:float(values[n]) for name,values in f['raw_features'].items()},
            residual_features={name:float(f[name][n]) for name in ('neighbor','community','clustering')},score=float(score[n])) for n in range(45)]
        return score

    def configuration(self):return dict(window=self.window,feature=self.feature,communities=self.communities)


class HypergraphModel(_PrefixModel):
    def __init__(self,window=52,support=2,shrinkage=5):
        if type(window) is not int or window not in WINDOWS or type(support) is not int or support not in (2,3) or type(shrinkage) is not int or shrinkage not in (5,10):
            raise ValueError('Outside declared hypergraph development grid')
        self.window,self.support,self.shrinkage=window,support,shrinkage

    def _scores(self,x):
        result=_hyper_context(x.tobytes(),x.shape,self.window,self.support,self.shrinkage)
        score=unit_residual(result['raw_scores'],result['counts']['frequency'])
        self.last_diagnostic=[dict(row,window=self.window,raw_score=float(result['raw_scores'][i]),
            relational_score=float(score[i])) for i,row in enumerate(result['diagnostics'])]
        return score

    def configuration(self):return dict(window=self.window,support=self.support,shrinkage=self.shrinkage)


class GraphHypergraphConsensus(_PrefixModel):
    def __init__(self,graph_model,hypergraph_model):self.graph_model,self.hypergraph_model=graph_model,hypergraph_model
    def _scores(self,x):
        from src.models.predictive import rank_numbers
        rankings=[rank_numbers(dict(enumerate(model._scores(x).tolist(),1))) for model in (self.graph_model,self.hypergraph_model)]
        self.last_diagnostic=[]
        return -(np.argsort(rankings[0])+np.argsort(rankings[1]))/2.
