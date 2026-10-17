"""H19 complete event-process search; each null chooses its own effects."""
from functools import lru_cache
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.analysis.point_process import (LAGS,SCHEMES,STATE_COUNTS,KERNELS,
    event_history,renewal_table,all_effects,kernel_effects)

FAMILIES=('renewal','self_positive','self_negative','cross_positive','cross_negative','kernel')
ALPHA=26
SUPPORT=30
RENEWAL_SUPPORT=20


@lru_cache(maxsize=1)
def _inventory():
    keys=[];families=[];metadata=[];indices=[]
    def add(family,kind,index,**parameters):
        keys.append(family+'/'+kind+'/'+','.join(f'{k}={v}' for k,v in sorted(parameters.items())))
        families.append(family);metadata.append(dict(family=family,kind=kind,**parameters));indices.append(index)
    for scheme in SCHEMES:
        for number in range(45):
            for state in range(STATE_COUNTS[scheme]):
                add('renewal','renewal_hazard',('renewal',scheme,number,state),scheme=scheme,number=number+1,state=state)
    for family in FAMILIES[1:5]:
        self_relation=family.startswith('self')
        for l,lag in enumerate(LAGS):
            for source in range(45):
                for target in ([source] if self_relation else [n for n in range(45) if n!=source]):
                    add(family,'lag_effect',('effect',l,source,target),lag=lag,source=source+1,target=target+1)
    for k,kernel in enumerate(KERNELS):
        for source in range(45):
            for target in range(45):
                add('kernel','lag_kernel',('kernel',k,source,target),kernel=kernel,source=source+1,target=target+1)
    return keys,families,metadata,indices


def _observation(raw,index):
    kind,a,b,c=raw['indices'][index];contexts=raw['contexts']
    if kind=='renewal':
        table=contexts['renewal'][a];base=np.asarray(table['baseline'])
        baseline=float(base[b] if base.ndim==1 else base[b,c])
        return dict(support=int(table['support'][b,c]),hits=int(table['hits'][b,c]),baseline=baseline,
            raw_rate=float(table['rate'][b,c]) if table['support'][b,c] else None,
            conditional=float(table['conditional'][b,c]),effect=float(table['effect'][b,c]),
            eligible=bool(table['eligible'][b,c]))
    if kind=='effect':
        table=contexts['effects'];idx=(a,b,c)
        return {key:(bool(table[key][idx]) if key=='eligible' else int(table[key][idx]) if key in ('support','hits') else
            float(table[key][idx]) if np.isfinite(table[key][idx]) else None)
            for key in ('support','hits','baseline','rate','conditional','lift','log_odds','effect','score','eligible')}
    table=contexts['kernel'];e=contexts['effects']
    return dict(amplitude=float(table['amplitude'][a,b,c]),support=int(np.min(e['support'][:,b,c])),
        lag_effects=e['effect'][:,b,c].tolist(),lag_scores=e['score'][:,b,c].tolist(),
        lag_supports=e['support'][:,b,c].astype(int).tolist(),eligible=bool(table['eligible'][a,b,c]))


def metric_vector(x,*,details=True):
    x=research_matrix(x)
    if len(x)<208:raise ValueError('Complete point-process search requires208..1245 draws')
    keys,families,metadata,indices=_inventory()
    renewal={scheme:renewal_table(x,scheme,alpha=ALPHA,minimum=RENEWAL_SUPPORT) for scheme in SCHEMES}
    effects=all_effects(x,alpha=ALPHA,minimum=SUPPORT)
    kernel=kernel_effects(x,alpha=ALPHA,minimum=SUPPORT,effects=effects)
    arrays=[]
    for scheme in SCHEMES:
        table=renewal[scheme];arrays.append(np.where(table['eligible'],table['score'],np.nan).ravel())
    diagonal=np.eye(45,dtype=bool)
    for family in FAMILIES[1:5]:
        mask=diagonal if family.startswith('self') else ~diagonal
        score=effects['score'][:,mask]
        oriented=np.maximum(score if family.endswith('positive') else -score,0.)
        arrays.append(np.where(effects['eligible'][:,mask],oriented,np.nan).ravel())
    arrays.append(np.where(kernel['eligible'],kernel['score'],np.nan).ravel())
    values=np.concatenate(arrays)
    raw=dict(draws=len(x),keys=keys,values=values,families=families,metadata=metadata,indices=indices,
        contexts=dict(renewal=renewal,effects=effects,kernel=kernel),representation_hash=sha256(x.tobytes()).hexdigest(),
        space=dict(cells=len(keys),family_cells={f:families.count(f) for f in FAMILIES},numbers=45,
            ordered_cross_pairs=1980,self_relations=45,lags=list(LAGS),schemes=list(SCHEMES),
            renewal_state_counts=dict(STATE_COUNTS),kernels=list(KERNELS),alpha=ALPHA,
            minimum_source_support=SUPPORT,minimum_renewal_support=RENEWAL_SUPPORT,
            kernel_relations=2025,kernel_candidates=6075))
    if len(values)!=len(keys):raise RuntimeError('Fixed inventory mismatch')
    raw['rows']=[dict(key=keys[i],**metadata[i],oriented_value=float(values[i]),**_observation(raw,i)) for i in range(len(keys))] if details else []
    return raw


def fit_calibration(n,*,replicates=32,seed=201001,progress=None):
    if type(n) is not int or not 208<=n<=1245:raise ValueError('Historical cutoff required')
    if type(replicates) is not int or replicates<4:raise ValueError('At least4 pilots required')
    vectors=[];raw=None
    for i in range(replicates):
        child=int(np.random.SeedSequence([seed,n,i]).generate_state(1)[0])
        raw=metric_vector(iid_surrogate(n,seed=child),details=False);vectors.append(raw['values'])
        if progress:progress(f'Calibration {n}: {i+1}/{replicates}')
    matrix=np.array(vectors);finite=np.isfinite(matrix);count=finite.sum(0)
    mean=np.divide(np.where(finite,matrix,0).sum(0),count,out=np.zeros(matrix.shape[1]),where=count>0)
    squared=np.where(finite,np.square(matrix-mean),0).sum(0)
    std=np.sqrt(np.divide(squared,count-1,out=np.zeros_like(mean),where=count>1))
    return dict(draws=n,replicates=replicates,seed=seed,keys=raw['keys'],families=raw['families'],metadata=raw['metadata'],space=raw['space'],
        mean=mean,std=std,finite_count=count,eligible=(count>=max(4,int(np.ceil(.75*replicates))))&(std>1e-12),pilot_values=matrix)


def standardize(raw,c):
    if raw['draws']!=c['draws'] or raw['keys']!=c['keys']:raise ValueError('Calibration cutoff/search identity mismatch')
    active=np.asarray(c['eligible'],bool)&np.isfinite(raw['values']);z=np.full(len(raw['keys']),np.nan)
    z[active]=(raw['values'][active]-np.asarray(c['mean'])[active])/np.asarray(c['std'])[active]
    return z


def complete_search(raw,c):
    z=standardize(raw,c);maxima={};leaders={};families=np.array(raw['families'])
    for family in FAMILIES:
        eligible=np.flatnonzero((families==family)&np.isfinite(z))
        if not len(eligible):raise ValueError(f'No eligible search cells: {family}')
        selected=int(eligible[np.argmax(z[eligible])]);maxima[family]=float(z[selected])
        leaders[family]=dict(key=raw['keys'][selected],z=float(z[selected]),oriented_value=float(raw['values'][selected]),
            **raw['metadata'][selected],**_observation(raw,selected))
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],eligible_cells=int(np.isfinite(z).sum()),
        representation_hash=raw['representation_hash'])


def _null_job(x,calibrations,kind,code,index,seed,include_development):
    result=dict(null_model=kind,replicate=index,rebuilt=True)
    for scope,n,actual in [('full',len(x),x)]+([('development',900,x[:900])] if include_development else []):
        child=int(np.random.SeedSequence([seed,code,index,n]).generate_state(1)[0])
        null=iid_surrogate(n,seed=child) if kind=='iid' else constrained_surrogate(actual,seed=child)
        # All gaps, renewal bins, pair counts and kernels come from this history.
        raw=metric_vector(null,details=False);found=complete_search(raw,calibrations[n])
        result[scope]=dict(found,seed=child,raw_values=raw['values'],changed_fraction=float((actual!=null).mean()))
    return result


def _initialize_worker(x,calibrations,include_development):
    global _WORKER_DATA
    _WORKER_DATA=x,calibrations,include_development


def _worker_job(job):
    x,c,dev=_WORKER_DATA
    return _null_job(x,c,*job,dev)


def null_search(x,calibrations,*,replicates=199,seed=200042,workers=1,include_development=True,progress=None):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    if include_development and len(x)!=1245:raise ValueError('Canonical full+development requires1..1245')
    c={n:{k:cal[k] for k in ('draws','keys','mean','std','eligible')} for n,cal in calibrations.items()}
    jobs=[(kind,code,i,seed) for kind,code in [('iid',0),('fixed_margins',1)] for i in range(replicates)];rows=[]
    def consume(iterator):
        for row in iterator:
            rows.append(row)
            if progress:progress(row)
    if workers==1:consume(_null_job(x,c,*job,include_development) for job in jobs)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers,initializer=_initialize_worker,initargs=(x,c,include_development)) as pool:
            consume(pool.map(_worker_job,jobs))
    return rows


def compare_maxima(real,rows,*,scope):
    table=[]
    for kind in ('iid','fixed_margins'):
        group=[row[scope] for row in rows if row['null_model']==kind]
        if not group:raise ValueError('Both null families required')
        for family in FAMILIES:
            observed=real['maxima'][family];null=np.array([row['maxima'][family] for row in group])
            exceed=int((null>=observed).sum());p=(1+exceed)/(len(null)+1)
            table.append(dict(scope=scope,cutoff=real['draws'],null_model=kind,family=family,real_max=observed,
                null_mean=float(null.mean()),null_q95=float(np.quantile(null,.95)),exceedances=exceed,replicates=len(null),
                global_p=p,adjusted_p=min(1,6*p)))
    return table
