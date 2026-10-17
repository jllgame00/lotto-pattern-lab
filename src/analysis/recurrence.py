"""Phase 11 causal geometry. Draw endpoints are ONE-based; arrays are zero-based."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import rankdata

CUTOFF = 1245


def research_matrix(x):
    x = np.asarray(x)
    if x.ndim != 2 or x.shape[1] != 45 or not 2 <= len(x) <= CUTOFF:
        raise ValueError('Phase 11 research requires 2..1245 draws of 45 numbers')
    if not np.isin(x, [0, 1]).all() or not np.all(x.sum(axis=1) == 6):
        raise ValueError('Exactly six binary main numbers per draw required')
    return x.astype(bool, copy=False)


@dataclass(frozen=True)
class EmbeddingConfig:
    family: str = 'A'
    window: int = 1
    m: int = 2
    tau: int = 1
    metric: str = 'hamming'

    def __post_init__(self):
        allowed = ('hamming', 'jaccard') if self.family == 'A' else ('euclidean', 'cosine')
        if (self.family not in ('A','B','C') or self.m not in (2,3,4) or
                self.tau not in (1,2,4,8,13,26) or self.metric not in allowed or
                self.window not in ((10,26,52) if self.family == 'C' else (1,))):
            raise ValueError('Outside predeclared embedding search')

    @property
    def span(self):
        return (self.m - 1) * self.tau + self.window - 1

    @property
    def dimension(self):
        return (13 if self.family == 'B' else 45) * self.m

    @property
    def key(self):
        return f'{self.family}_W{self.window}_m{self.m}_t{self.tau}_{self.metric}'


def configurations():
    return [EmbeddingConfig(f,w,m,t,d)
            for f in ('A','B','C') for w in ((10,26,52) if f == 'C' else (1,))
            for m in (2,3,4) for t in (1,2,4,8,13,26)
            for d in (('hamming','jaccard') if f == 'A' else ('euclidean','cosine'))]


def observations(x, config):
    x = research_matrix(x)
    if config.family == 'A':
        return x.astype(float)
    if config.family == 'C':
        w = config.window
        c = np.vstack((np.zeros((1,45)), np.cumsum(x, axis=0)))
        out = np.full(x.shape, np.nan)
        out[w-1:] = (c[w:] - c[:-w]) / w
        return out
    numbers = (np.nonzero(x)[1] + 1).reshape(-1,6)
    spacing = np.diff(numbers, axis=1)
    return np.column_stack((numbers.sum(1), numbers.mean(1), numbers.std(1),
        numbers[:,0], numbers[:,-1], np.ptp(numbers,axis=1), spacing.mean(1),
        spacing.std(1), spacing.min(1), spacing.max(1), (spacing==1).sum(1),
        (numbers%2==1).sum(1), (numbers<=22).sum(1))).astype(float)


def fit_scaler(o, cutoff):
    if not 1 <= cutoff <= len(o):
        raise ValueError('Scaler cutoff outside available training history')
    train = o[:cutoff]
    train = train[np.isfinite(train).all(axis=1)]
    if not len(train):
        raise ValueError('Insufficient scaler history')
    mean, scale = train.mean(0), train.std(0)
    return mean, np.where(scale < 1e-12, 1., scale)


def embed(o, config, scaler=None):
    if len(o) <= config.span:
        raise ValueError('Insufficient complete embedding history')
    values = (o-scaler[0])/scaler[1] if scaler is not None else o
    indices = np.arange(config.span, len(o))[:,None] - np.arange(config.m)*config.tau
    result = values[indices].reshape(len(indices), -1)
    if not np.isfinite(result).all():
        raise ValueError('Incomplete embedding history')
    return result, np.arange(config.span+1, len(o)+1)


def distances(a, b, metric):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if metric == 'cosine':
        an, bn = np.linalg.norm(a,axis=1), np.linalg.norm(b,axis=1)
        result = 1 - (a / np.where(an==0,1,an)[:,None]) @ (b / np.where(bn==0,1,bn)[:,None]).T
        result[np.ix_(an==0,bn==0)] = 0
        return np.clip(result,0,2)
    if metric not in ('euclidean','hamming','jaccard'):
        raise ValueError('Unknown metric')
    if metric in ('hamming','jaccard'):
        # Binary support algebra avoids a coordinate loop for every pair.
        if not np.isin(a,[0,1]).all() or not np.isin(b,[0,1]).all():
            raise ValueError('Binary distances require 0/1 coordinates')
        shared=a@b.T
        total=a.sum(1)[:,None]+b.sum(1)[None,:]
        mismatch=np.maximum(0,total-2*shared)
        if metric=='hamming': return mismatch/a.shape[1]
        union=total-shared
        return mismatch/np.where(union==0,1,union)
    return cdist(a,b,metric=metric)


def eligible(endpoints, config, length=1):
    ends = np.asarray(endpoints)
    return np.abs(ends[:,None]-ends[None,:]) > config.span + length


def recurrence_matrix(d, valid, construction, *, k=10, density=.1):
    d, valid = np.asarray(d), np.asarray(valid,bool)
    if d.shape != valid.shape or d.ndim != 2 or d.shape[0] != d.shape[1]:
        raise ValueError('Square matching distance and eligibility matrices required')
    valid = valid & ~np.eye(len(d),dtype=bool)
    r = np.zeros_like(valid)
    if construction == 'knn':
        if k < 1: raise ValueError('Positive k required')
        order = np.argsort(np.where(valid,d,np.inf),axis=1,kind='stable')[:,:k]
        r[np.arange(len(d))[:,None],order] = True
        r &= valid
        return r | r.T
    if construction != 'density' or not 0 < density < 1:
        raise ValueError('Unknown recurrence construction or density')
    i,j = np.nonzero(np.triu(valid,1))
    order = np.argsort(d[i,j],kind='stable')[:int(len(i)*density)]
    r[i[order],j[order]] = True
    return r | r.T


def _line_lengths(r, diagonal):
    previous = np.zeros_like(r)
    if diagonal: previous[1:,1:] = r[:-1,:-1]
    else: previous[1:] = r[:-1]
    i,j = np.nonzero(r & ~previous)
    lengths = np.zeros(len(i),int)
    active = np.arange(len(i))
    while len(active):
        lengths[active] += 1
        i[active] += 1
        if diagonal: j[active] += 1
        active = active[(i[active]<len(r)) & (j[active]<r.shape[1])]
        active = active[r[i[active],j[active]]]
    return lengths


def rqa(r, valid=None, minimum=2):
    r = np.asarray(r,bool)
    count = int(r.sum())
    diagonal = _line_lengths(r,True); vertical = _line_lengths(r,False)
    diag = diagonal[diagonal>=minimum]; vert = vertical[vertical>=minimum]
    if len(diag):
        _,counts = np.unique(diag,return_counts=True); p = counts/counts.sum()
        entropy = float(-(p*np.log(p)).sum())
    else: entropy = 0.
    i,j = np.nonzero(r)
    times = np.diff(j)[np.diff(i)==0]
    denominator = int(np.asarray(valid).sum()) if valid is not None else r.size
    return dict(recurrence_rate=count/denominator if denominator else 0.,
        det=float(diag.sum()/count) if count else 0.,
        mean_diagonal=float(diag.mean()) if len(diag) else 0.,
        lmax=int(diagonal.max()) if len(diagonal) else 0,
        diagonal_entropy=entropy, laminarity=float(vert.sum()/count) if count else 0.,
        trapping_time=float(vert.mean()) if len(vert) else 0.,
        recurrence_time_mean=float(times.mean()) if len(times) else 0.,
        recurrence_time_median=float(np.median(times)) if len(times) else 0.,
        recurrence_time_std=float(times.std()) if len(times) else 0.,
        recurrence_time_cv=float(times.std()/times.mean()) if len(times) else 0.,
        recurrence_time_count=len(times))


def rank_correlation(a,b):
    a,b = rankdata(a),rankdata(b)
    a,b = a-a.mean(),b-b.mean()
    denom = np.linalg.norm(a)*np.linalg.norm(b)
    return float(a@b/denom) if denom else 0.


def successor_diagnostic(x, ends, d, valid, *, details=False):
    x = research_matrix(x)
    ends = np.asarray(ends)
    if len(ends)!=len(d) or np.any(ends>=len(x)) or np.any(ends<1):
        raise ValueError('Each state must have an available successor')
    successors = x[ends].astype(float)  # endpoint j -> zero-based row j == draw j+1
    overlaps = successors @ successors.T
    i,j = np.nonzero(np.triu(valid,1)); ds, hits = d[i,j], overlaps[i,j]
    if not len(i): raise ValueError('No eligible successor pairs')
    jac = hits/(12-hits)
    past = valid & (ends[None,:] < ends[:,None])
    available = past.any(axis=1)
    nearest = np.argmin(np.where(past,d,np.inf),axis=1)
    nn = overlaps[np.arange(len(ends))[available],nearest[available]]
    result = dict(successor=-rank_correlation(ds,hits), spearman=rank_correlation(ds,hits),
        spearman_jaccard=rank_correlation(ds,jac), ordinary_overlap=float(hits.mean()),
        ordinary_jaccard=float(jac.mean()), nearest_overlap=float(nn.mean()) if len(nn) else 0.,
        nearest_jaccard=float((nn/(12-nn)).mean()) if len(nn) else 0., pairs=len(hits))
    if details:
        # Equal-distance ties remain together; deciles may be empty for discrete metrics.
        edges = np.quantile(ds,np.arange(.1,1,.1)); bins = np.searchsorted(edges,ds,side='left')
        result['deciles'] = [dict(decile=b+1,count=int((bins==b).sum()),
            distance=float(ds[bins==b].mean()),overlap=float(hits[bins==b].mean()),
            jaccard=float(jac[bins==b].mean())) for b in range(10) if np.any(bins==b)]
    return result


def concentration(d, valid):
    pair = d[np.triu(valid,1)]
    nearest = np.min(np.where(valid,d,np.inf),axis=1)
    nearest = nearest[np.isfinite(nearest)]
    median = float(np.median(pair)) if len(pair) else 0.
    return dict(distance_median=median, distance_std=float(pair.std()) if len(pair) else 0.,
        distance_variance=float(pair.var()) if len(pair) else 0.,
        nearest_median=float(np.median(nearest)) if len(nearest) else 0.,
        nearest_q10=float(np.quantile(nearest,.1)) if len(nearest) else 0.,
        nearest_q90=float(np.quantile(nearest,.9)) if len(nearest) else 0.,
        nearest_median_ratio=float(np.median(nearest)/median) if median and len(nearest) else 0.)
