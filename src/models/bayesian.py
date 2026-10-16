"""Beta appearance tendencies, with optional exponential fractional counts."""
import numpy as np
import pandas as pd
from scipy.stats import beta
from src.models.predictive import FittedModel


def observation_matrix(rows):
    table=rows.pivot(index='target_draw',columns='number',values='appeared_next').sort_index()
    if (table.isna().any().any() or list(table.columns)!=list(range(1,46)) or
            not np.all(np.diff(table.index)==1)):
        raise ValueError('Requires contiguous complete 45-number observations')
    return table.to_numpy(float)


class OnlineModel(FittedModel):
    """Observe only the previous draw, encoded causally by current_gap == 0.

    Repeated scoring is idempotent; skipping an observation or going backwards
    is rejected. Parameters stay frozen between fits; state/counts update online.
    """
    def __init__(self,**kwargs): super().__init__(columns=['current_gap'],**kwargs)

    def advance(self,rows):
        self._current(rows)
        target=int(rows.target_draw.iloc[0]); observed=target-1
        if observed not in (self.observed_cutoff,self.observed_cutoff+1):
            raise ValueError('Online scoring requires consecutive targets without missing observations')
        if observed>self.observed_cutoff:
            self.observe(rows.sort_values('number').current_gap.eq(0).to_numpy(float))
            self.observed_cutoff=observed


class BayesianModel(OnlineModel):
    def __init__(self,*,alpha=2.,beta_prior=13.,half_life=None,**kwargs):
        super().__init__(**kwargs)
        if min(alpha,beta_prior)<=0 or (half_life is not None and half_life<=0):
            raise ValueError('Positive prior parameters and half-life required')
        self.alpha0,self.beta0,self.half_life=alpha,beta_prior,half_life
        self.decay=1. if half_life is None else 2**(-1/half_life)

    def fit(self,rows,*,cutoff):
        self._training(rows,cutoff)
        if rows.target_draw.max()!=cutoff: raise ValueError('Online fit must end at cutoff')
        x=observation_matrix(rows)
        weights=self.decay**np.arange(len(x)-1,-1,-1)
        self.successes=weights@x; self.observations=float(weights.sum())
        self.observed_cutoff=cutoff
        return self

    def observe(self,y):
        self.successes=self.decay*self.successes+y
        self.observations=self.decay*self.observations+1

    def score_rows(self,rows):
        self.advance(rows)
        values=(self.alpha0+self.successes)/(self.alpha0+self.beta0+self.observations)
        return dict(zip(range(1,46),values.tolist()))

    def diagnostics(self):
        a=self.alpha0+self.successes; b=self.beta0+self.observations-self.successes
        lo,hi=beta.ppf(np.array([.025,.975])[:,None],a,b)
        return pd.DataFrame(dict(number=np.arange(1,46),observations=self.observations,
            prior_alpha=self.alpha0,prior_beta=self.beta0,alpha=a,beta=b,posterior_mean=a/(a+b),ci_low=lo,ci_high=hi))

    def configuration(self):
        return dict(super().configuration(),alpha=self.alpha0,beta=self.beta0,half_life=self.half_life,
                    note='Fractional-count recency intervals are descriptive, not calibrated evidence')
