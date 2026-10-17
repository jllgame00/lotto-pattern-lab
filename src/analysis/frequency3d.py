"""Recent-frequency pre-draw states; no gap state is calculated or combined."""
import numpy as np
import pandas as pd
from src.analysis.spatiotemporal import binary_matrix,lotto_matrix,P

WINDOWS=(10,26,52)

def frequency_states(x,window):
    x=binary_matrix(x)
    if window not in WINDOWS or type(window) is not int or len(x)>1245: raise ValueError('Bounded history and predeclared window required')
    prefix=np.vstack([np.zeros((1,45),int),np.cumsum(x,axis=0)])
    count=np.full(prefix.shape,np.nan); count[window:]=prefix[window:]-prefix[:-window]
    rate=count/window
    prior=np.divide(prefix,np.arange(len(prefix))[:,None],out=np.full(prefix.shape,np.nan),where=np.arange(len(prefix))[:,None]>0)
    relative=np.divide(rate,prior,out=np.full(prefix.shape,np.nan),where=prior>0)
    return dict(count=count,rate=rate,prior_rate=prior,relative=relative,
                deviation_uniform=rate-P,deviation_historical=rate-prior)

class FrequencyEncoder:
    def __init__(self,window=26):
        if type(window) is not int or window not in WINDOWS: raise ValueError('Window must be10,26,52')
        self.window=window

    def fit(self,features,*,cutoff):
        if type(cutoff) is not int or not self.window<cutoff<=1245 or any(v.shape!=(cutoff,45) for v in features.values()):
            raise ValueError('Fit requires exactly the training pre-states')
        finite=features['count'][np.isfinite(features['count'])]
        if not len(finite) or ((finite<0)|(finite>self.window)|(finite!=np.floor(finite))).any(): raise ValueError('Invalid or insufficient counts')
        self.edges=np.quantile(finite,[1/3,2/3],method='higher').tolist();self.cutoff=cutoff
        return self

    def transform(self,features,representation='quantile'):
        if representation not in ('count','rate','quantile','relative'): raise ValueError('Unknown frequency representation')
        values=features['relative'] if representation=='relative' else features['count']
        valid=np.isfinite(values);result=np.full(values.shape,-1,np.int16)
        if representation in ('count','rate'): result[valid]=values[valid].astype(int)
        else: result[valid]=np.searchsorted([.5,1.5] if representation=='relative' else self.edges,values[valid],side='left')
        return result

    def count(self,representation): return self.window+1 if representation in ('count','rate') else 3

    def configuration(self):
        return dict(version='pre-draw-frequency-v1',window=self.window,training_cutoff=self.cutoff,
            quantile_edges=self.edges,quantile_method='higher; boundary ties lower',relative_edges=[.5,1.5],
            missing_state=-1,minimum_history=self.window,timing='state t uses draws t-W..t-1 only',
            historical_rate='all completed draws before target; zero denominator relative is missing')

def frequency_table(history,*,cutoff):
    x=lotto_matrix(history,cutoff=cutoff); frames=[]
    for window in WINDOWS:
        f=frequency_states(x,window)
        frames.append(pd.DataFrame(dict(target_draw=np.repeat(np.arange(1,cutoff+1),45),
            feature_cutoff=np.repeat(np.arange(cutoff),45),number=np.tile(np.arange(1,46),cutoff),window=window,
            appeared_next=x.ravel().astype(int),**{k:v[:-1].ravel() for k,v in f.items()})))
    return pd.concat(frames,ignore_index=True)
