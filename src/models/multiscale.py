"""Training-prefix multiscale experiments; neutral fallback is recent frequency."""
from functools import lru_cache
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.wavelet import PERIODS,morlet_transform,localized_regions
from src.analysis.ssa import WINDOWS,decompose,candidate_pairs,recurrent_forecast

SCALE_SETS=((8,13,20,26,39,52),(13,20,26,39,52,78),(20,26,39,52,78,104))


@lru_cache(maxsize=1)
def _transform(raw,shape):
    x=np.frombuffer(raw,dtype=np.bool_).reshape(shape)
    periods=tuple(p for p in PERIODS if p<=len(x)/4)
    return morlet_transform(x.astype(float),periods=periods)


def wavelet_scores(x,periods,min_cycles):
    """COI-safe region supports a scale; trailing harmonic OLS estimates phase.

    The CWT is never evaluated at an unsupported future/boundary coefficient.
    At least two observed cycles are used by OLS, then only one step is predicted.
    Unsupported numbers retain W26 frequency; outputs are scores, not calibrated p.
    """
    x=x[-416:];n=len(x);base=x[-26:].mean(0)
    t=_transform(x.tobytes(),x.shape)
    keep=np.isin(t['periods'],periods)
    selected={**t,'periods':np.asarray(t['periods'])[keep],
        'power':t['power'][:,keep], 'coefficients':t['coefficients'][:,keep],
        'valid':t['valid'][keep]}
    regions=localized_regions(selected,min_cycles=min_cycles,threshold=4.)
    scores=base.copy();chosen={}
    for region in regions:
        i=region['series'];p=region['period']
        if region['end']<n-2*p:continue
        if i not in chosen or region['score']>chosen[i]['score']:chosen[i]=region
    for i,region in chosen.items():
        p=region['period'];length=min(n,int(np.ceil(min_cycles*p)))
        time=np.arange(n-length,n);angle=2*np.pi*time/p
        design=np.column_stack((np.ones(length),np.cos(angle),np.sin(angle)))
        beta=np.linalg.lstsq(design,x[-length:,i],rcond=None)[0]
        fitted=design@beta;variance=np.var(x[-length:,i])
        r2=1-np.mean((x[-length:,i]-fitted)**2)/max(variance,1e-12)
        if r2>=.1:
            next_value=beta@[1,np.cos(2*np.pi*n/p),np.sin(2*np.pi*n/p)]
            scores[i]=np.clip(next_value,0,1)
    return scores


@lru_cache(maxsize=3)
def _ssa_both(raw,shape,length):
    x=np.frombuffer(raw,dtype=np.bool_).reshape(shape);base=x[-26:].mean(0)
    scores={rule:base.copy() for rule in ('leading2','supported_pair')}
    for i in range(45):
        result=decompose(x[:,i].astype(float),length,components=8)
        pairs=candidate_pairs(result,min_period=8,max_period=min(104,len(x)/4))
        indices={'leading2':[0,1]}
        if pairs:
            best=max(pairs,key=lambda p:p['score']);indices['supported_pair']=[best['first'],best['second']]
        for rule,selected in indices.items():
            try:
                prediction=float(np.asarray(recurrent_forecast(result,selected,steps=1)).ravel()[0])
            except ValueError:
                continue
            if np.isfinite(prediction):scores[rule][i]=np.clip(prediction,0,1)
    return scores


def ssa_scores(x,length,rule):
    x=x[-416:]
    return _ssa_both(x.tobytes(),x.shape,length)[rule].copy()


class _PrefixModel:
    def fit(self,x,*,cutoff):
        x=research_matrix(x)
        if type(cutoff) is not int or cutoff!=len(x) or len(x)<208:
            raise ValueError('Exact sufficient training prefix required')
        self.training=x.copy();self.training_cutoff=cutoff
        return self

    def score_matrix(self,x,*,target):
        x=research_matrix(x)
        if (type(target) is not int or target!=len(x)+1 or target>1245 or
            target<=self.training_cutoff or not np.array_equal(x[:self.training_cutoff],self.training)):
            raise ValueError('Historical target<=1245 with unchanged prefix ending T-1 required')
        return dict(enumerate(self._scores(x).tolist(),1))


class WaveletPhaseModel(_PrefixModel):
    def __init__(self,periods=SCALE_SETS[0],min_cycles=2):
        if tuple(periods) not in SCALE_SETS or min_cycles not in (2,3):raise ValueError('Outside Wavelet development grid')
        self.periods=tuple(periods);self.min_cycles=min_cycles
    def _scores(self,x):return wavelet_scores(x,self.periods,self.min_cycles)


class SSAModel(_PrefixModel):
    def __init__(self,length=52,rule='supported_pair'):
        if length not in WINDOWS or rule not in ('leading2','supported_pair'):raise ValueError('Outside SSA development grid')
        self.length=length;self.rule=rule
    def _scores(self,x):return ssa_scores(x,self.length,self.rule)


class MultiscaleConsensusModel(_PrefixModel):
    def __init__(self,wavelet,ssa):self.wavelet=wavelet;self.ssa=ssa
    def _scores(self,x):
        from src.models.predictive import rank_numbers
        rankings=[rank_numbers(dict(enumerate(model._scores(x).tolist(),1))) for model in (self.wavelet,self.ssa)]
        return -(np.argsort(rankings[0])+np.argsort(rankings[1]))/2.
