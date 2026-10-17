"""Transparent causal finite-axis scores, not calibrated winning probabilities."""
from dataclasses import dataclass,asdict
import numpy as np
from scipy.stats import rankdata
from src.analysis.number_space import matrix,rolling_counts,smooth,ranges,WINDOWS,WIDTHS,PRIMARY_KERNELS,P


@dataclass(frozen=True)
class NumberSpaceConfig:
    window:int=26
    kernel:str='triangular1'
    width:int=5
    neighbor_only:bool=False
    prior_draws:float=26.

    def __post_init__(self):
        if (self.window not in WINDOWS or self.kernel not in PRIMARY_KERNELS or self.width not in WIDTHS or
            type(self.neighbor_only) is not bool or self.neighbor_only and self.kernel=='none' or self.prior_draws!=26.):
            raise ValueError('Only predeclared windows/kernels/widths and prior26 are supported')


class NeighborhoodModel:
    def __init__(self,**kwargs):self.config=NumberSpaceConfig(**kwargs)

    def fit(self,x,*,cutoff):
        x=matrix(x)
        if type(cutoff) is not int or cutoff!=len(x) or cutoff<max(104,self.config.window):
            raise ValueError('Fit requires sufficient and exact training prefix')
        self.training=x.copy();self.training_cutoff=cutoff
        return self

    def _past(self,x,target):
        x=matrix(x)
        if (type(target) is not int or target!=len(x)+1 or target>1246 or target<=self.training_cutoff or
            not np.array_equal(x[:self.training_cutoff],self.training)):
            raise ValueError('Use unchanged training prefix and only draws before target')
        return x

    def score_matrix(self,x,*,target):
        x=self._past(x,target);c=self.config
        rate=rolling_counts(x,c.window)[-1]/c.window
        return dict(enumerate(smooth(rate,c.kernel,neighbor_only=c.neighbor_only).tolist(),1))

    def configuration(self):
        return dict(model=type(self).__name__,version='phase10-number-space-v1',**asdict(self.config),
            boundary='truncate and normalize remaining weights; never wrap',timing='target t uses completed draws<t',
            score='causal recent appearance rate smoothed on finite number axis')


class RangeDensityModel(NeighborhoodModel):
    def score_matrix(self,x,*,target):
        x=self._past(x,target);c=self.config
        counts=rolling_counts(x,c.window)[-1]
        r=ranges(c.width);excess=[]
        for a,b in r:
            rate=(counts[a-1:b].sum()/c.width+c.prior_draws*P)/(c.window+c.prior_draws)
            excess.append(max(0.,rate-P))
        total=np.zeros(45);denom=np.zeros(45)
        for (a,b),weight in zip(r,excess):total[a-1:b]+=weight;denom[a-1:b]+=1
        return dict(enumerate((P+total/denom).tolist(),1))

    def configuration(self):
        return dict(super().configuration(),score='p+mean containing-range positive excess; prior26 draws at p')


def rank_mix(gap,neighborhood,gap_weight):
    if gap_weight not in (.25,.5,.75):raise ValueError('Only predeclared weights .25/.5/.75')
    values=[]
    for scores in (gap,neighborhood):
        if set(scores)!=set(range(1,46)) or not np.isfinite(list(scores.values())).all():raise ValueError('Full45 finite scores required')
        values.append((rankdata([scores[n] for n in range(1,46)],method='average')-1)/44)
    return dict(enumerate((gap_weight*values[0]+(1-gap_weight)*values[1]).tolist(),1))


class GapNeighborhoodModel(NeighborhoodModel):
    def __init__(self,*,gap_weight=.5,**kwargs):
        super().__init__(**kwargs)
        if gap_weight not in (.25,.5,.75):raise ValueError('Predeclared combination weight required')
        self.gap_weight=gap_weight

    def fit(self,x,*,cutoff,feature_rows):
        super().fit(x,cutoff=cutoff)
        if feature_rows.empty or feature_rows.target_draw.max()>cutoff:raise ValueError('Gap training labels must precede prediction')
        from src.models.predictive import LogisticModel
        from src.analysis.features import GAP
        from src.prediction_scope import ProspectiveScope
        self.gap=LogisticModel(columns=GAP,prediction_scope=ProspectiveScope(cutoff)).fit(feature_rows,cutoff=cutoff)
        return self

    def score_matrix(self,x,*,target,current_rows):
        self._past(x,target)
        from src.prediction_scope import ProspectiveScope
        self.gap.prediction_scope=ProspectiveScope(target-1)
        return rank_mix(self.gap.score_rows(current_rows),super().score_matrix(x,target=target),self.gap_weight)

    def configuration(self):
        return dict(super().configuration(),gap_weight=self.gap_weight,normalization='equal-tie percentile rank',
            score='gap_weight*gap_logistic_rank+(1-gap_weight)*neighborhood_rank')
