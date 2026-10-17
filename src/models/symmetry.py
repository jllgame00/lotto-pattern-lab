"""Causal experimental fixed-center mirror activity regression, H16.

Historical model only. Target23 is a neutral reference, not self-prediction.
No Gap features, secondary shifts or prospective publication are included.
"""
from functools import lru_cache
import numpy as np
from src.analysis.recurrence import research_matrix

WINDOWS=(10,26,52)
LAGS=(1,2,3,4,8,13,26,52)
P=6/45


@lru_cache(maxsize=3)
def _rates(raw,shape,window):
    x=np.frombuffer(raw,dtype=np.bool_).reshape(shape)
    cumulative=np.vstack((np.zeros((1,45)),np.cumsum(x,axis=0)))
    return (cumulative[window:]-cumulative[:-window])/window


@lru_cache(maxsize=24)
def _context(raw,shape,window,lag):
    x=np.frombuffer(raw,dtype=np.bool_).reshape(shape);rates=_rates(raw,shape,window)
    # Source rate ending draw u predicts completed outcome u+lag. The last
    # training outcome is N; query source ends N+1-lag, never later than N.
    source=rates[:-lag,::-1];target=x[window-1+lag:]
    source_mean=source.mean(axis=0);target_mean=target.mean(axis=0)
    centered=source-source_mean;response=target-target_mean
    binary=x[window-1:len(x)-lag,::-1]
    return dict(source_mean=source_mean,target_mean=target_mean,
        covariance=(centered*response).sum(axis=0),variance=np.square(centered).sum(axis=0),
        source_events=binary.sum(axis=0),hits=(binary&target).sum(axis=0),
        query=rates[len(rates)-lag,::-1],source_draw=len(x)+1-lag,samples=len(target))


class MirrorModel:
    """One pooled ridge slope after removing per-number training means.

    A source-support factor s/(s+shrinkage) attenuates unstable candidates.
    The same shrinkage supplies fixed IID-scaled ridge pseudo-observations.
    Every score recomputes the fit on its exact available prefix, even when
    the outer comparison engine invokes fit less often.
    """
    def __init__(self,window=26,lag=1,shrinkage=50,support=20):
        if (type(window) is not int or window not in WINDOWS or type(lag) is not int or lag not in LAGS
            or type(shrinkage) is not int or shrinkage not in (50,200) or type(support) is not int or support!=20):
            raise ValueError('Outside predeclared H16 model grid')
        self.window,self.lag,self.shrinkage,self.support=window,lag,shrinkage,support

    def fit(self,x,*,cutoff):
        x=research_matrix(x)
        if type(cutoff) is not int or cutoff!=len(x) or cutoff<208:raise ValueError('Exact training prefix>=208 required')
        self.training=x.copy();self.training_cutoff=cutoff;return self

    def score_matrix(self,x,*,target):
        x=research_matrix(x)
        if (not hasattr(self,'training_cutoff') or type(target) is not int or target!=len(x)+1 or target>1245
            or target<=self.training_cutoff or not np.array_equal(x[:self.training_cutoff],self.training)):
            raise ValueError('Historical target<=1245 requires unchanged completed prefix endingT-1')
        c=_context(x.tobytes(),x.shape,self.window,self.lag)
        supported=c['source_events']>=self.support;supported[22]=False
        total_variance=float(c['variance'][supported].sum())
        penalty=self.shrinkage*int(supported.sum())*P*(1-P)/self.window
        beta=float(np.clip(c['covariance'][supported].sum()/(total_variance+penalty),-1,1)) if total_variance>1e-12 else 0.
        weights=np.where(supported,c['source_events']/(c['source_events']+self.shrinkage),0.)
        deviation=c['query']-c['source_mean'];contributions=beta*weights*deviation
        contributions[22]=0.;scores=P+contributions
        self.pooled_coefficient=beta;self.score_training_cutoff=len(x)
        rates=np.divide(c['hits'],c['source_events'],out=np.full(45,np.nan),where=c['source_events']>0)
        self.last_diagnostic=[dict(number=j+1,mirror=45-j,window=self.window,lag=self.lag,
            shrinkage=self.shrinkage,source_draw=c['source_draw'],training_cutoff=len(x),samples=c['samples'],
            source_events=int(c['source_events'][j]),supported=bool(supported[j]),
            source_activity=float(c['query'][j]),training_source_mean=float(c['source_mean'][j]),
            training_target_mean=float(c['target_mean'][j]),training_conditional_rate=float(rates[j]) if np.isfinite(rates[j]) else None,
            training_mirror_lift=float(rates[j]/c['target_mean'][j]) if c['target_mean'][j]>0 and np.isfinite(rates[j]) else None,
            pooled_coefficient=beta,shrink_weight=float(weights[j]),deviation=float(deviation[j]),
            contribution=float(contributions[j]),score=float(scores[j])) for j in range(45)]
        if not np.isfinite(scores).all():raise ValueError('Finite45-number mirror scores required')
        return dict(enumerate(scores.tolist(),1))

    def configuration(self):return dict(window=self.window,lag=self.lag,shrinkage=self.shrinkage,support=self.support)
