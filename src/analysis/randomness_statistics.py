"""Compact Lotto-valid classical statistics. No textbook Bernoulli p-values."""
from functools import lru_cache
from itertools import combinations
from math import comb
import numpy as np
from .recurrence import research_matrix
from .complexity_encoding import lz78
from .spatiotemporal import iid_surrogate

LAGS=(1,2,3,4,8,13,26)
SHAPE_LAGS=(1,2,4,8,13,26)
SHAPE_NAMES=('sum','range','std','spacing_mean','spacing_std','consecutive_pairs','odd_count')
PAIRS=np.array(list(combinations(range(45),2)))
TRIPLES=np.array(list(combinations(range(45),3)))
PAIR6=np.array(list(combinations(range(6),2)))
TRIPLE6=np.array(list(combinations(range(6),3)))
SHAPE_BINS=(np.linspace(20,256,13),np.array([4,10,20,25,30,35,40,45]),
    np.array([0,4,6,8,10,12,14,16,18,23]),np.arange(.5,10),
    np.array([0,1,2,3,4,5,6,8,12,20]),np.arange(-.5,6),np.arange(-.5,7))


def shape_from_numbers(a):
    a=np.asarray(a,float);gap=np.diff(a,axis=1)
    return np.column_stack((a.sum(1),np.ptp(a,axis=1),a.std(1),gap.mean(1),gap.std(1),
        (gap==1).sum(1),(a%2==1).sum(1)))


def representations(x):
    x=research_matrix(x);a=(np.nonzero(x)[1]+1).reshape(-1,6)
    bands=np.array([((a>=lo)&(a<=lo+8)).sum(1) for lo in (1,10,19,28,37)]).T
    return dict(binary=x,numbers=a,gaps=np.diff(a,axis=1),shape=shape_from_numbers(a),bands=bands)


@lru_cache(maxsize=1)
def shape_reference():
    # Synthetic auxiliary sample, not external/future historical draws.
    x=iid_surrogate(65536,seed=260001);a=(np.nonzero(x)[1]+1).reshape(-1,6)
    shape=shape_from_numbers(a)
    return dict(probabilities=[np.histogram(shape[:,i],bins=b)[0]/len(shape) for i,b in enumerate(SHAPE_BINS)],
        median=np.median(shape,axis=0),seed=260001,synthetic_draw_count=65536)


def entropy(counts):
    c=np.asarray(counts,float);p=c[c>0]/c.sum() if c.sum() else np.empty(0)
    return float(-np.sum(p*np.log2(p)))


def likelihood_ratio(observed,expected):
    observed=np.asarray(observed,float);expected=np.asarray(expected,float);active=(observed>0)&(expected>0)
    return float(2*np.sum(observed[active]*np.log(observed[active]/expected[active])))


def pearson(observed,expected):
    observed=np.asarray(observed,float);expected=np.asarray(expected,float);active=expected>0
    return float(np.sum((observed[active]-expected[active])**2/expected[active]))


def lag_correlation(s,lag):
    a=np.asarray(s,float)
    if not 1<=lag<len(a):raise ValueError('Lag outside completed sequence')
    left=a[:-lag]-a[:-lag].mean();right=a[lag:]-a[lag:].mean()
    scale=np.linalg.norm(left)*np.linalg.norm(right)
    return float(np.clip(np.dot(left,right)/scale,-1,1)) if scale else 0.


def binary_word_counts(s,length):
    s=np.asarray(s,int)
    if s.ndim!=1 or not np.isin(s,[0,1]).all() or not 1<=length<=4 or length>len(s):raise ValueError('Binary words1..4 required')
    code=np.zeros(len(s)-length+1,int)
    for j in range(length):code=2*code+s[j:j+len(code)]
    return np.bincount(code,minlength=2**length)


def transition_g(s):
    c=binary_word_counts(s,2).reshape(2,2);expected=c.sum(1)[:,None]*c.sum(0)[None,:]/c.sum()
    return likelihood_ratio(c,expected)


def word_g(s,length):
    s=np.asarray(s,int);p=s.mean();codes=np.arange(2**length)
    ones=np.array([int(v).bit_count() for v in codes]);prob=p**ones*(1-p)**(length-ones)
    return likelihood_ratio(binary_word_counts(s,length),(len(s)-length+1)*prob)


def conditional_difference(s):
    c=binary_word_counts(s,2).reshape(2,2);row=c.sum(1)
    p=np.divide(c[:,1],row,out=np.zeros(2),where=row>0)
    return float(abs(p[1]-p[0])) if np.all(row>0) else 0.


def run_lengths(s):
    s=np.asarray(s)
    starts=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1]
    return s[starts],np.diff(np.r_[starts,len(s)])


def number_gap_statistics(s):
    s=np.asarray(s,int);values,lengths=run_lengths(s);gaps=np.diff(np.flatnonzero(s));p=s.mean()
    absence=int(lengths[values==0].max()) if np.any(values==0) else 0
    appearance=int(lengths[values==1].max()) if np.any(values==1) else 0
    edges=np.array([1,2,3,4,5,6,9,14,27,53,np.inf]);observed=np.histogram(gaps,bins=edges)[0]
    survival=np.where(np.isfinite(edges),(1-p)**(edges-1),0.) if 0<p<1 else np.r_[1.,np.zeros(len(edges)-1)]
    probability=survival[:-1]-survival[1:]
    return dict(absence=absence,appearance=appearance,runs=len(lengths),gaps=gaps,
        gap_gof=pearson(observed,len(gaps)*probability),
        gap_cv2=float(gaps.var()/gaps.mean()**2) if len(gaps)>1 else 0.)


def overlap_probabilities():
    return np.array([comb(6,k)*comb(39,6-k)/comb(45,6) for k in range(7)])


def overlap_statistics(x,lag):
    x=research_matrix(x)
    if not 1<=lag<len(x):raise ValueError('Lag outside history')
    overlap=(x[:-lag]&x[lag:]).sum(1);hist=np.bincount(overlap,minlength=7);prob=overlap_probabilities()
    pooled=np.r_[hist[:3],hist[3:].sum()];expected=len(overlap)*np.r_[prob[:3],prob[3:].sum()]
    return dict(overlaps=overlap,counts=hist,expected=len(overlap)*prob,mean=float(overlap.mean()),
        variance=float(overlap.var()),jaccard=float(np.mean(overlap/(12-overlap))),gof=pearson(pooled,expected),maximum=int(overlap.max()))


def pair_triple_counts(x):
    x=research_matrix(x);integer=x.astype(np.int32);cross=integer.T@integer
    pair_counts=cross[PAIRS[:,0],PAIRS[:,1]]
    numbers=np.nonzero(x)[1].reshape(-1,6);triples=numbers[:,TRIPLE6]
    code=(triples[:,:,0]*45+triples[:,:,1])*45+triples[:,:,2]
    all_counts=np.bincount(code.ravel(),minlength=45**3)
    wanted=(TRIPLES[:,0]*45+TRIPLES[:,1])*45+TRIPLES[:,2]
    return PAIRS,pair_counts,TRIPLES,all_counts[wanted]


def difference_probabilities():
    return np.arange(44,0,-1)/comb(45,2)


def adjacent_gap_probabilities():
    return np.array([comb(45-d,5)/comb(45,6) for d in range(1,41)])


def spacing_statistics(numbers):
    a=np.asarray(numbers,int);n=len(a);diff=(a[:,PAIR6[:,1]]-a[:,PAIR6[:,0]]).ravel()
    counts=np.bincount(diff,minlength=45)[1:45];p=difference_probabilities()
    gaps=np.diff(a,axis=1);hist=np.bincount(gaps.ravel(),minlength=41)[1:41];gap_p=adjacent_gap_probabilities()
    grouped=np.r_[hist[:8],hist[8:12].sum(),hist[12:20].sum(),hist[20:].sum()]
    expected=n*5*np.r_[gap_p[:8],gap_p[8:12].sum(),gap_p[12:20].sum(),gap_p[20:].sum()]
    normalized=gaps/gaps.sum(1)[:,None]
    return dict(counts=counts,difference_gof=pearson(counts,n*15*p),adjacent_gof=pearson(grouped,expected),
        concentration=float(np.mean(np.sum((normalized-.2)**2,axis=1))))


def entropy_deficit(s,length):
    s=np.asarray(s,int);h=entropy(np.bincount(s,minlength=2))
    return float(length*h-entropy(binary_word_counts(s,length)))


def spectral_statistics(s):
    s=np.asarray(s,float);power=abs(np.fft.rfft(s-s.mean()))[1:14]**2
    if power.sum()==0:return 0.,0.
    concentration=power.max()/power.sum()
    flatness=np.exp(np.mean(np.log(np.maximum(power,1e-300))))/power.mean()
    return float(concentration),float(1-flatness)


def normalized_lz(s):
    s=np.asarray(s,int);h=entropy(np.bincount(s,minlength=2))
    return float(lz78(s,2)['normalized']/h) if h>0 else 0.
