"""Causal pre-draw gap states. Missing means never seen, not an ordinary gap."""
import numpy as np
import pandas as pd
from src.analysis.spatiotemporal import binary_matrix,lotto_matrix


def causal_states(x):
    """Rows0..T predict draws1..T+1. For target t, gap=t-1-last draw.

    Outcomes at t update state t+1 only. Historical mean gap is the mean of
    completed intervals between at least two appearances strictly before t.
    """
    x=binary_matrix(x); size=len(x); times=np.arange(size)[:,None]
    last=np.vstack([np.full((1,45),-1),np.maximum.accumulate(np.where(x,times,-1),axis=0)])
    first=np.vstack([np.full((1,45),size),np.minimum.accumulate(np.where(x,times,size),axis=0)])
    count=np.vstack([np.zeros((1,45),int),np.cumsum(x,axis=0)])
    gap=np.arange(size+1)[:,None]-1-last
    gap=np.where(last>=0,gap,np.nan).astype(float)
    mean=np.divide(last-first,count-1,out=np.full(gap.shape,np.nan),where=count>=2)
    relative=np.divide(gap,mean,out=np.full(gap.shape,np.nan),where=np.isfinite(mean)&(mean>0))
    return gap,mean,relative


class GapEncoder:
    """Fit once on training pre-states; transformation never updates boundaries."""
    def fit(self,gap,relative,*,cutoff):
        gap=np.asarray(gap); relative=np.asarray(relative)
        if gap.shape!=relative.shape or gap.ndim!=2 or gap.shape!=(cutoff,45) or not 1<=cutoff<=1245:
            raise ValueError('Encoder requires exactly the declared training pre-states')
        finite=gap[np.isfinite(gap)]
        if not len(finite) or (finite<0).any() or (finite!=np.floor(finite)).any():
            raise ValueError('Insufficient or invalid historical gap observations')
        self.cutoff=int(cutoff)
        self.cap=int(min(26,np.ceil(np.quantile(finite,.95))))
        self.edges=np.quantile(finite,[1/3,2/3],method='higher').tolist()
        return self

    def transform(self,gap,relative,representation='quantile'):
        gap=np.asarray(gap); relative=np.asarray(relative)
        if gap.shape!=relative.shape: raise ValueError('Gap/relative shapes differ')
        values=relative if representation=='relative' else gap
        valid=np.isfinite(values); out=np.full(gap.shape,-1,dtype=np.int16)
        if representation=='clipped': out[valid]=np.minimum(values[valid],self.cap).astype(int)
        elif representation in ('quantile','relative'):
            out[valid]=np.searchsorted(self.edges if representation=='quantile' else [.5,1.5],values[valid],side='left')
        else: raise ValueError('Unknown gap representation')
        return out

    def count(self,representation): return self.cap+1 if representation=='clipped' else 3

    def configuration(self):
        return dict(version='pre-draw-gap-v1',training_cutoff=self.cutoff,clip_quantile=.95,
            clip_hard_limit=26,clip_cap=self.cap,quantile_probabilities=[1/3,2/3],quantile_edges=self.edges,
            quantile_method='higher',relative_edges=[.5,1.5],missing_state=-1,
            timing='target t uses draws<t; gap=t-1-last_appearance_draw',
            exact_state_definition='integers0..cap; cap includes all larger finite gaps')


def state_table(history,*,cutoff):
    x=lotto_matrix(history,cutoff=cutoff); g,m,r=causal_states(x)
    return pd.DataFrame(dict(target_draw=np.repeat(np.arange(1,cutoff+1),45),
        feature_cutoff=np.repeat(np.arange(cutoff),45),number=np.tile(np.arange(1,46),cutoff),
        current_gap=g[:-1].ravel(),historical_mean_gap=m[:-1].ravel(),relative_gap=r[:-1].ravel(),
        appeared_next=x.ravel().astype(int)))
