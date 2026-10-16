"""Pooled empirical gap hazards; fixed bins and training-only Beta shrinkage."""
import numpy as np
import pandas as pd
from scipy.stats import beta
from src.models.predictive import FittedModel
from src.research_seal import assert_open

EDGES={'gap':[1,3,5,8,13,20,30], 'ratio':[.25,.5,1,1.5,2,3,4],
       'zscore':[-1,-.5,0,.5,1,2,3]}


def hazard_bucket(values,kind='gap'):
    if kind not in EDGES: raise ValueError('Unknown hazard variable')
    x=np.asarray(values,dtype=float)
    return np.where(np.isfinite(x),np.searchsorted(EDGES[kind],x,side='right'),-1)


def hazard_values(rows,kind):
    if kind in ('gap','exact'): return rows.current_gap.to_numpy(float)
    if kind=='ratio': return rows.gap_ratio.to_numpy(float)
    if kind=='zscore':
        return ((rows.current_gap+1-rows.mean_gap)/rows.gap_std.replace(0,np.nan)).to_numpy(float)
    raise ValueError('Unknown hazard variable')


def hazard_table(rows,*,min_count=200):
    assert_open(rows,'target_draw')
    records=[]
    eras=[('all',rows)]
    for label,targets in zip(('early','middle','recent'),np.array_split(np.sort(rows.target_draw.unique()),3)):
        eras.append((label,rows[rows.target_draw.isin(targets)]))
    for era,group in eras:
        for kind in ('exact','gap','ratio','zscore'):
            values=hazard_values(group,kind)
            bins=values if kind=='exact' else hazard_bucket(values,kind)
            frame=pd.DataFrame({'bucket':bins,'y':group.appeared_next.to_numpy()})
            for bucket,g in frame[np.isfinite(bins)&(bins!=-1)].groupby('bucket'):
                n=len(g); s=int(g.y.sum()); low,high=beta.ppf([.025,.975],s+.5,n-s+.5)
                records.append(dict(era=era,variable=kind,bucket=float(bucket),observations=n,
                    appearances=s,probability=s/n,ci_low=low,ci_high=high,deviation=s/n-6/45,
                    adequate=n>=min_count,interval='Jeffreys marginal; dependent number rows, not a significance test'))
    return pd.DataFrame(records)


class GapHazardModel(FittedModel):
    def __init__(self,*,kind='gap',prior_strength=75,**kwargs):
        super().__init__(columns=['current_gap','gap_ratio','mean_gap','gap_std'],**kwargs)
        if kind not in EDGES or prior_strength<=0: raise ValueError('Invalid hazard configuration')
        self.kind,self.prior_strength=kind,prior_strength

    def fit(self,rows,*,cutoff):
        self._training(rows,cutoff)
        bins=hazard_bucket(hazard_values(rows,self.kind),self.kind)
        self.counts=np.bincount(bins[bins>=0],minlength=8)
        self.successes=np.bincount(bins[bins>=0],weights=rows.appeared_next.to_numpy()[bins>=0],minlength=8)
        self.probabilities=(self.successes+self.prior_strength*6/45)/(self.counts+self.prior_strength)
        return self

    def score_rows(self,rows):
        self._current(rows)
        bins=hazard_bucket(hazard_values(rows,self.kind),self.kind)
        scores=np.where(bins>=0,self.probabilities[np.maximum(bins,0)],6/45)
        return dict(zip(rows.number.astype(int),scores.tolist()))

    def configuration(self):
        return dict(super().configuration(),kind=self.kind,edges=EDGES[self.kind],prior_strength=self.prior_strength)
