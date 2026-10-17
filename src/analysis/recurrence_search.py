"""Full-search parity: each history rebuilds observations, scaling and geometry."""
from dataclasses import asdict
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import (research_matrix,configurations,observations,embed,
    fit_scaler,distances,eligible,recurrence_matrix,rqa,successor_diagnostic,concentration)
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate

FAMILIES = ('det','lmax','laminarity','recurrence_time_cv','successor')
SEARCH_SPACE = dict(embeddings=180,recurrence_definitions=2,families=5,
    cells=1800,unique_cells=1620,nearest_candidates=180,analog_candidates=1440,continuation_candidates=2880)


def complete_search(x, *, start=661, end=899, scale_end=400):
    x = research_matrix(x)
    if not 130 <= scale_end < start < end < len(x):
        raise ValueError('Invalid training/scaler/structural successor boundaries')
    cache={}; rows=[]; maxima={f:-np.inf for f in FAMILIES}; leaders={}
    digest=sha256()
    for c in configurations():
        key=(c.family,c.window)
        if key not in cache:
            cache[key]=observations(x,c);digest.update(cache[key].tobytes())
        o=cache[key]
        scaler=fit_scaler(o,scale_end) if c.metric=='euclidean' else None
        e,ends=embed(o,c,scaler); keep=(ends>=start)&(ends<=end)
        e,ends=e[keep],ends[keep]
        d=distances(e,e,c.metric);valid=eligible(ends,c)
        if not np.triu(valid,1).any(): raise ValueError('Structural interval too short for every configuration')
        successor=successor_diagnostic(x,ends,d,valid)
        conc=concentration(d,valid)
        for construction in ('knn','density'):
            q=rqa(recurrence_matrix(d,valid,construction),valid)
            row=dict(key=c.key,**asdict(c),dimension=c.dimension,construction=construction,
                **q,**successor,**conc)
            rows.append(row)
            for family in FAMILIES:
                if row[family]>maxima[family]:
                    maxima[family]=row[family];leaders[family]=dict(config=asdict(c),construction=construction,value=row[family])
    return dict(maxima=maxima,leaders=leaders,rows=rows,space=SEARCH_SPACE,
        observation_hash=digest.hexdigest())


def _null_job(job):
    x,kind,code,i,seed,search_args=job
    child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
    null=iid_surrogate(len(x),seed=child) if code==0 else constrained_surrogate(x,seed=child)
    result=complete_search(null,**(search_args or {}))
    if result['space']!=SEARCH_SPACE: raise RuntimeError('Search parity failure')
    return dict(null_model=kind,replicate=i,seed=child,rebuilt=True,configurations=180,
        observation_hash=result['observation_hash'],**result['maxima'])


def null_search(x, *, replicates=199,seed=110042,search_args=None,progress=None,workers=1):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1: raise ValueError('Positive surrogate count required')
    if type(workers) is not int or workers<1: raise ValueError('Positive worker count required')
    jobs=[(x,kind,code,i,seed,search_args) for kind,code in [('iid',0),('fixed_margins',1)] for i in range(replicates)]
    rows=[]
    def consume(iterator):
        for row in iterator:
            rows.append(row)
            if progress: progress(row)
    if workers==1: consume(map(_null_job,jobs))
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers) as pool: consume(pool.map(_null_job,jobs))
    return rows


def compare_maxima(real,rows):
    result=[]
    for kind in ('iid','fixed_margins'):
        group=[r for r in rows if r['null_model']==kind]
        for family in FAMILIES:
            values=np.array([r[family] for r in group]); value=real['maxima'][family]
            exceed=int((values>=value).sum());p=(exceed+1)/(len(values)+1)
            result.append(dict(null_model=kind,family=family,real_max=value,null_mean=float(values.mean()),
                null_q95=float(np.quantile(values,.95)),exceedances=exceed,replicates=len(values),
                global_p=p,adjusted_p=min(1.,5*p)))
    return result
