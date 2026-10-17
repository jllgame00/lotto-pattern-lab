"""H16 fixed mirror search, independent pilot calibration, own-max nulls."""
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.analysis.symmetry import (LAGS,SHIFTS,draw_metrics,pooled_relation,pair_relations,
    activity_correlations,rolling_symmetry)

FAMILIES=('same_draw','pooled','pair','asymmetry','regime','anti','shift')


def metric_vector(x,*,details=True):
    x=research_matrix(x)
    if len(x)<208:raise ValueError('H16 complete search needs at least208 completed draws')
    keys=[];values=[];families=[];metadata=[];rows=[]
    def add(family,kind,value,**parameters):
        key=kind+'/'+','.join(f'{k}={v}' for k,v in sorted(parameters.items()))
        meta=dict(family=family,kind=kind,**parameters)
        keys.append(key);values.append(float(value));families.append(family);metadata.append(meta)
        if details:rows.append(dict(key=key,**meta,oriented_value=float(value),eligible=bool(np.isfinite(value))))
    draw=draw_metrics(x)
    for kind,value in [('mean_pairs',draw['pairs'].mean()),('mean_symmetry',draw['symmetry'].mean()),
        ('mean_jaccard',draw['jaccard'].mean()),('fraction_multiple_pairs',(draw['pairs']>=2).mean())]:add('same_draw',kind,value)
    add('anti','mean_side_imbalance',draw['imbalance'].mean())
    for lag in LAGS:
        pooled=pooled_relation(x,lag)
        add('pooled','pooled_risk',pooled['risk_difference'],lag=lag)
        add('anti','negative_pooled_risk',-pooled['risk_difference'],lag=lag)
        pairs=pair_relations(x,lag)
        valid=np.asarray(pairs['eligible'],dtype=bool)
        for j,(source,target) in enumerate(zip(pairs['source'],pairs['target'])):
            value=pairs['risk_difference'][j] if valid[j] else np.nan
            add('pair','pair_risk',value,lag=lag,source=int(source),target=int(target))
            add('anti','negative_pair_risk',-value,lag=lag,source=int(source),target=int(target))
        rates=np.asarray(pairs['rate']).reshape(22,2);eligible=valid.reshape(22,2)
        for pair in range(22):
            value=abs(rates[pair,0]-rates[pair,1]) if eligible[pair].all() else np.nan
            add('asymmetry','directional_difference',value,lag=lag,pair=pair+1)
    movements=activity_correlations(x)
    for row in movements:
        params={k:row[k] for k in ('pair','window','lag','direction')}
        value=row['correlation'] if row['eligible'] else np.nan
        add('pair','positive_activity_correlation',value,**params)
        add('anti','negative_activity_correlation',-value,**params)
    regimes=rolling_symmetry(x)
    for row in regimes:
        for kind in ('mean_pairs','mean_symmetry','mean_imbalance','mean_correlation'):
            add('regime','rolling_'+kind,row[kind],window=row['window'],endpoint=row['endpoint'])
    for shift in SHIFTS:
        for lag in LAGS:
            add('shift','shift_pooled_risk',pooled_relation(x,lag,shift=shift)['risk_difference'],shift=shift,lag=lag)
    return dict(draws=len(x),keys=keys,values=np.array(values),families=families,metadata=metadata,rows=rows,
        representation_hash=sha256(x.tobytes()).hexdigest(),space=dict(cells=len(keys),family_cells={f:families.count(f) for f in FAMILIES},
        mirror_pairs=22,directions=44,lags=list(LAGS),activity_correlations=len(movements),regime_windows=len(regimes),shifts=list(SHIFTS)))


def fit_calibration(n,*,replicates=32,seed=181001,progress=None):
    if type(replicates) is not int or replicates<4:raise ValueError('At least4 independent pilots required')
    if type(n) is not int or not 208<=n<=1245:raise ValueError('Calibration requires bounded208..1245 history')
    vectors=[];raw=None
    for i in range(replicates):
        child=int(np.random.SeedSequence([seed,n,i]).generate_state(1)[0])
        raw=metric_vector(iid_surrogate(n,seed=child),details=False);vectors.append(raw['values'])
        if progress:progress(f'Calibration {n}: {i+1}/{replicates}')
    matrix=np.array(vectors);finite=np.isfinite(matrix).sum(0)
    mean=np.nanmean(matrix,axis=0);std=np.nanstd(matrix,axis=0,ddof=1)
    eligible=(finite>=max(4,int(np.ceil(.75*replicates))))&(std>1e-12)
    return dict(keys=raw['keys'],families=raw['families'],metadata=raw['metadata'],draws=n,replicates=replicates,seed=seed,
        mean=mean,std=std,eligible=eligible,finite_count=finite,pilot_values=matrix,space=raw['space'])


def standardize(raw,calibration):
    if raw['draws']!=calibration['draws'] or raw['keys']!=calibration['keys']:raise ValueError('Calibration cutoff/search identity mismatch')
    z=np.full(len(raw['keys']),np.nan);mask=np.asarray(calibration['eligible'],dtype=bool)&np.isfinite(raw['values'])
    z[mask]=(raw['values'][mask]-np.asarray(calibration['mean'])[mask])/np.asarray(calibration['std'])[mask]
    return z


def complete_search(raw,calibration):
    z=standardize(raw,calibration);maxima={};leaders={}
    for family in FAMILIES:
        indices=np.flatnonzero((np.array(raw['families'])==family)&np.isfinite(z))
        if not len(indices):raise ValueError(f'No eligible {family} search cell')
        selected=int(indices[np.argmax(z[indices])]);maxima[family]=float(z[selected])
        leaders[family]=dict(key=raw['keys'][selected],z=float(z[selected]),oriented_value=float(raw['values'][selected]),**raw['metadata'][selected])
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],
        eligible_cells=int(np.isfinite(z).sum()),representation_hash=raw['representation_hash'])


def _null_job(x,calibrations,kind,code,index,seed,include_development):
    result=dict(null_model=kind,replicate=index,rebuilt=True)
    for scope,n,actual in [('full',len(x),x)]+([('development',900,x[:900])] if include_development else []):
        child=int(np.random.SeedSequence([seed,code,index,n]).generate_state(1)[0])
        null=iid_surrogate(n,seed=child) if kind=='iid' else constrained_surrogate(actual,seed=child)
        raw=metric_vector(null,details=False);found=complete_search(raw,calibrations[n])
        result[scope]=dict(found,seed=child,raw_values=raw['values'],changed_fraction=float((actual!=null).mean()))
    return result


def _initialize_worker(x,calibrations,include_development):
    global _WORKER_DATA
    _WORKER_DATA=(x,calibrations,include_development)


def _worker_job(job):
    x,c,dev=_WORKER_DATA
    return _null_job(x,c,*job,dev)


def null_search(x,calibrations,*,replicates=199,seed=180042,workers=1,include_development=True,progress=None):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive null counts required')
    if include_development and len(x)!=1245:raise ValueError('Full+development search requires exact1..1245')
    c={n:{k:cal[k] for k in ('keys','draws','mean','std','eligible')} for n,cal in calibrations.items()}
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
    output=[]
    for kind in ('iid','fixed_margins'):
        group=[r[scope] for r in rows if r['null_model']==kind]
        if not group:raise ValueError('Both established null families required')
        for family in FAMILIES:
            null=np.array([r['maxima'][family] for r in group]);observed=real['maxima'][family]
            exceed=int((null>=observed).sum());p=(1+exceed)/(len(null)+1)
            output.append(dict(scope=scope,cutoff=real['draws'],null_model=kind,family=family,real_max=observed,
                null_mean=float(null.mean()),null_q95=float(np.quantile(null,.95)),exceedances=exceed,
                replicates=len(null),global_p=p,adjusted_p=min(1.,7*p)))
    return output
