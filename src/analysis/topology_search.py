"""Predeclared H0 search with exact per-cell point counts and local scalers."""
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import numpy as np
from .recurrence import research_matrix
from .spatiotemporal import iid_surrogate,constrained_surrogate
from .topology import WINDOWS,H1_STATUS,configurations,build_cloud,rolling_endpoints,h0_persistence,distance_diagnostics

FAMILIES=('h0_longest','h0_total','h0_entropy','h0_tail')
SUMMARIES=('longest','total','entropy','tail')


def metric_vector(x,*,details=True):
    x=research_matrix(x);n=len(x)
    if n<208:raise ValueError('Topology search requires208..1245 historical draws')
    intervals=[('whole',0,1,n)]
    for w in WINDOWS:
        if w<=n:intervals.extend(('rolling',w,int(end-w+1),int(end)) for end in rolling_endpoints(n,w))
    keys=[];families=[];metadata=[];values=[];clouds=[];counts=[];inventory=[]
    for location,w,start,end in intervals:
        for config in configurations():
            cloud=build_cloud(x,config,start=start,end=end);d=cloud.pop('distances')
            persistence=h0_persistence(d);diagnostic=distance_diagnostics(d)
            index=len(counts);counts.append(cloud['point_count'])
            meta=dict(config=config.key,location=location,window=w,start=start,end=end,points=cloud['point_count'],cloud_index=index)
            inventory.append(meta)
            for family,summary in zip(FAMILIES,SUMMARIES):
                keys.append(f'{family}|{location}|{w}|{end}|{config.key}');families.append(family)
                metadata.append(dict(family=family,summary=summary,**meta));values.append(persistence[summary])
            if details:clouds.append(dict(cloud,**meta,persistence=persistence,distance_diagnostic=diagnostic))
    space=dict(cells=len(keys),clouds=len(counts),configs=[c.key for c in configurations()],windows=list(WINDOWS),stride=104,
        rolling_fits=len(intervals)-1,point_counts=counts,family_cells={f:families.count(f) for f in FAMILIES},h1_status=H1_STATUS,
        activity_point_stride='26/52 nonoverlap, end aligned',tail_fraction=.1)
    raw=dict(draws=n,keys=keys,families=families,metadata=metadata,values=np.array(values),space=space,inventory=inventory,
             representation_hash=sha256(x.tobytes()).hexdigest())
    if details:raw['clouds']=clouds
    return raw


def fit_calibration(n,*,replicates=32,seed=231001,progress=None):
    if type(n) is not int or not 208<=n<=1245 or type(replicates) is not int or replicates<4:
        raise ValueError('Historical cutoff and at least four pilots required')
    vectors=[]
    for i in range(replicates):
        child=int(np.random.SeedSequence([seed,n,i]).generate_state(1)[0])
        raw=metric_vector(iid_surrogate(n,seed=child),details=False);vectors.append(raw['values'])
        if progress:progress(f'Pilot {n}: {i+1}/{replicates}')
    a=np.array(vectors);finite=np.isfinite(a);count=finite.sum(0)
    mean=np.divide(np.where(finite,a,0).sum(0),count,out=np.zeros(a.shape[1]),where=count>0)
    std=np.sqrt(np.divide(np.where(finite,(a-mean)**2,0).sum(0),count-1,out=np.zeros_like(mean),where=count>1))
    return dict(draws=n,replicates=replicates,seed=seed,keys=raw['keys'],families=raw['families'],metadata=raw['metadata'],space=raw['space'],
        mean=mean,std=std,finite_count=count,eligible=(count>=max(4,int(np.ceil(.75*replicates))))&(std>1e-12),pilot_values=a)


def standardize(raw,c):
    if raw['draws']!=c['draws'] or raw['keys']!=c['keys']:raise ValueError('Calibration scope/search mismatch')
    active=np.asarray(c['eligible'])&np.isfinite(raw['values']);z=np.full(len(raw['keys']),np.nan)
    z[active]=(raw['values'][active]-np.asarray(c['mean'])[active])/np.asarray(c['std'])[active]
    entropy=np.array(raw['families'])=='h0_entropy';z[entropy]=abs(z[entropy])
    return z


def complete_search(raw,c):
    z=standardize(raw,c);families=np.array(raw['families']);maxima={};leaders={}
    for family in FAMILIES:
        indices=np.flatnonzero((families==family)&np.isfinite(z))
        if not len(indices):raise ValueError(f'No supported H0 family {family}')
        i=int(indices[np.argmax(z[indices])]);maxima[family]=float(z[i])
        leaders[family]=dict(index=i,key=raw['keys'][i],value=float(raw['values'][i]),z=float(z[i]),**raw['metadata'][i])
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],eligible_cells=int(np.isfinite(z).sum()),representation_hash=raw['representation_hash'])


def _null_job(x,c,kind,code,i,seed,dev):
    row=dict(null_model=kind,replicate=i)
    for scope,n,actual in [('full',len(x),x)]+([('development',900,x[:900])] if dev else []):
        child=int(np.random.SeedSequence([seed,code,i,n]).generate_state(1)[0])
        null=iid_surrogate(n,seed=child) if kind=='iid' else constrained_surrogate(actual,seed=child)
        raw=metric_vector(null,details=False)
        row[scope]=dict(complete_search(raw,c[n]),seed=child,rebuilt=True,raw_values=raw['values'],
            changed_fraction=float((actual!=null).mean()),row_six=bool((null.sum(1)==6).all()),
            fixed_margins_preserved=bool(np.array_equal(actual.sum(0),null.sum(0))) if kind!='iid' else None)
    return row


def _initialize(x,c,dev):
    global _WORKER
    _WORKER=x,c,dev


def _job(job):
    x,c,dev=_WORKER;return _null_job(x,c,*job,dev)


def null_search(x,calibrations,*,replicates=199,seed=230042,workers=1,include_development=True,progress=None):
    x=research_matrix(x)
    if include_development and len(x)!=1245:raise ValueError('Full+development requires exact1..1245')
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    c={n:{k:v[k] for k in ('draws','keys','mean','std','eligible')} for n,v in calibrations.items()}
    jobs=[(kind,code,i,seed) for kind,code in [('iid',0),('fixed_margins',1)] for i in range(replicates)];rows=[]
    def collect(iterator):
        for row in iterator:
            rows.append(row)
            if progress:progress(row)
    if workers==1:collect(_null_job(x,c,*job,include_development) for job in jobs)
    else:
        with ProcessPoolExecutor(max_workers=workers,initializer=_initialize,initargs=(x,c,include_development)) as pool:collect(pool.map(_job,jobs,chunksize=1))
    return rows


def compare_maxima(real,rows,*,scope='full'):
    out=[]
    for kind in ('iid','fixed_margins'):
        selected=[r[scope] for r in rows if r['null_model']==kind]
        if not selected:raise ValueError('Both null families required')
        for family in FAMILIES:
            a=np.array([r['maxima'][family] for r in selected]);obs=real['maxima'][family]
            p=(1+int((a>=obs).sum()))/(len(a)+1)
            out.append(dict(scope=scope,null_model=kind,family=family,real_max=obs,null_median=float(np.median(a)),
                global_p=p,adjusted_p=min(1.,4*p),replicates=len(a)))
    return out


def development_selection(x,c,rows):
    x=research_matrix(x)
    if len(x)!=900 or c['draws']!=900:raise ValueError('Development requires exact1..900')
    found=complete_search(metric_vector(x,details=False),c);comparison=compare_maxima(found,rows,scope='development')
    passing=[f for f in FAMILIES if all(r['adjusted_p']<=.05 for r in comparison if r['family']==f)]
    selected=found['leaders'][passing[0]] if passing else None
    rolling=bool(selected and selected['location']=='rolling')
    return dict(training_cutoff=900,training_hash=sha256(x.tobytes()).hexdigest(),later_start=901,
        passing_families=passing,selected_cell=selected,structural_gate_passed=bool(passing),causal_mapping_evaluated=False,
        predictive_model_justified=False,decision='REVIEW_CAUSAL_MAPPING' if rolling else 'PREDICTIVE_MODEL_NOT_JUSTIFIED',
        reason='Structure alone is insufficient; causal stable regimes/outcome mapping required' if passing else 'No corrected development H0 evidence',
        ensemble_decision='NOT CURRENTLY JUSTIFIED',comparison=comparison,h1_status=H1_STATUS)
