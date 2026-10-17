"""H20 fixed complete search; every null rebuilds every representation."""
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import iid_surrogate, constrained_surrogate
from src.analysis.long_memory import dfa, crossover, rs_estimate
from src.analysis.long_memory_series import build_series, aggregation, spectral_slope, rolling_endpoints

PRIMARY=('persistent','anti_persistent','crossover','aggregation','rolling','whole_system')
SECONDARY=('rs_reference','spectral_secondary','dfa2_sensitivity')
FAMILIES=PRIMARY+SECONDARY
WINDOWS=(312,416,624)


def metric_vector(x, *, details=True):
    x=research_matrix(x)
    if len(x)<312:raise ValueError('H20 requires312..1245 historical draws')
    rep=build_series(x);v=rep['values'];n=len(x)
    curve=dfa(v);cross=crossover(curve);agg=aggregation(v)
    rs=rs_estimate(v);spec=spectral_slope(v);sensitivity=dfa(v,order=2)
    keys=[];families=[];metadata=[];values=[]
    def add(family,j,value,**extra):
        meta=dict(family=family,series=rep['names'][j],group=rep['groups'][j],column=j,**extra)
        keys.append('|'.join(str(t) for t in (family,j,*extra.values())))
        families.append(family);metadata.append(meta);values.append(float(value))
    for j in range(55):add('persistent',j,curve['alpha'][j])
    for j in range(55):add('anti_persistent',j,-curve['alpha'][j])
    for b,boundary in enumerate(cross['boundaries']):
        for j in range(55):add('crossover',j,cross['improvement'][b,j],boundary=int(boundary))
    for j in range(55):add('aggregation',j,agg['deviation'][j])
    rolling=[]
    for window in WINDOWS:
        if window > n:
            continue
        for end in rolling_endpoints(n,window):
            local=dfa(v[end-window:end]);rolling.append(dict(window=window,end=int(end),alpha=local['alpha']))
            for j in range(55):add('rolling',j,abs(local['alpha'][j]-.5),window=window,start=int(end-window+1),end=int(end))
    for j in range(45,55):add('whole_system',j,abs(curve['alpha'][j]-.5))
    for j in range(55):add('rs_reference',j,abs(rs['exponent'][j]-.5))
    for j in range(55):add('spectral_secondary',j,abs(spec['beta'][j]))
    for j in range(55):add('dfa2_sensitivity',j,abs(sensitivity['alpha'][j]-.5))
    raw=dict(draws=n,keys=keys,families=families,metadata=metadata,values=np.array(values),
        representation_hash=rep['representation_hash'],space=dict(cells=len(keys),series=55,numbers=45,
            shape_series=5,band_series=5,dfa_scales=curve['scales'].tolist(),detrending_order=1,
            minimum_segments=4,crossover_boundaries=cross['boundaries'].tolist(),rolling_windows=list(WINDOWS),
            rolling_stride=52,rolling_fits=len(rolling),family_cells={f:families.count(f) for f in FAMILIES}))
    if details:raw.update(representations=rep,curve=curve,cross=cross,aggregation=agg,rs=rs,spectral=spec,
                          sensitivity=sensitivity,rolling=rolling)
    return raw


def fit_calibration(n, *, replicates=32,seed=211001,progress=None):
    if type(n) is not int or not 312<=n<=1245:raise ValueError('Historical cutoff312..1245 required')
    if type(replicates) is not int or replicates<4:raise ValueError('At least4 independent pilots required')
    vectors=[]
    for i in range(replicates):
        child=int(np.random.SeedSequence([seed,n,i]).generate_state(1)[0])
        raw=metric_vector(iid_surrogate(n,seed=child),details=False);vectors.append(raw['values'])
        if progress:progress(f'Calibration {n}: {i+1}/{replicates}')
    a=np.array(vectors);finite=np.isfinite(a);count=finite.sum(0)
    mean=np.divide(np.where(finite,a,0).sum(0),count,out=np.zeros(a.shape[1]),where=count>0)
    std=np.sqrt(np.divide(np.where(finite,(a-mean)**2,0).sum(0),count-1,out=np.zeros_like(mean),where=count>1))
    return dict(draws=n,replicates=replicates,seed=seed,keys=raw['keys'],families=raw['families'],
        metadata=raw['metadata'],space=raw['space'],mean=mean,std=std,finite_count=count,
        eligible=(count>=max(4,int(np.ceil(.75*replicates))))&(std>1e-12),pilot_values=a)


def standardize(raw,c):
    if raw['draws']!=c['draws'] or raw['keys']!=c['keys']:raise ValueError('Calibration cutoff/search mismatch')
    active=np.asarray(c['eligible'])&np.isfinite(raw['values']);out=np.full(len(raw['keys']),np.nan)
    out[active]=(raw['values'][active]-np.asarray(c['mean'])[active])/np.asarray(c['std'])[active]
    return out


def complete_search(raw,c):
    """Require every family to have support (complete crossover needs N>=416)."""
    z=standardize(raw,c);families=np.array(raw['families']);maxima={};leaders={}
    for family in FAMILIES:
        active=np.flatnonzero((families==family)&np.isfinite(z))
        if not len(active):raise ValueError(f'No supported search cell: {family}')
        i=int(active[np.argmax(z[active])]);maxima[family]=float(z[i])
        leaders[family]=dict(index=i,key=raw['keys'][i],z=float(z[i]),value=float(raw['values'][i]),**raw['metadata'][i])
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],
        eligible_cells=int(np.isfinite(z).sum()),representation_hash=raw['representation_hash'])


def _null_job(x,c,kind,code,i,seed,dev):
    row=dict(null_model=kind,replicate=i,rebuilt=True)
    for scope,n,actual in [('full',len(x),x)]+([('development',900,x[:900])] if dev else []):
        child=int(np.random.SeedSequence([seed,code,i,n]).generate_state(1)[0])
        null=iid_surrogate(n,seed=child) if kind=='iid' else constrained_surrogate(actual,seed=child)
        raw=metric_vector(null,details=False)
        row[scope]=dict(complete_search(raw,c[n]),seed=child,raw_values=raw['values'],
            changed_fraction=float((actual!=null).mean()),row_six=bool((null.sum(1)==6).all()),
            fixed_margins_preserved=bool(np.array_equal(actual.sum(0),null.sum(0))) if kind!='iid' else None)
    return row


def _initialize(x,c,dev):
    global _WORKER
    _WORKER=x,c,dev


def _job(job):
    x,c,dev=_WORKER
    return _null_job(x,c,*job,dev)


def null_search(x,calibrations,*,replicates=199,seed=210042,workers=1,include_development=True,progress=None):
    x=research_matrix(x)
    if include_development and len(x)!=1245:raise ValueError('Canonical full+development requires1..1245')
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    c={n:{k:v[k] for k in ('draws','keys','mean','std','eligible')} for n,v in calibrations.items()}
    jobs=[(kind,code,i,seed) for kind,code in [('iid',0),('fixed_margins',1)] for i in range(replicates)]
    rows=[]
    if workers==1:
        iterator=(_null_job(x,c,*job,include_development) for job in jobs)
        for row in iterator:
            rows.append(row)
            if progress:progress(row)
    else:
        with ProcessPoolExecutor(max_workers=workers,initializer=_initialize,initargs=(x,c,include_development)) as pool:
            for row in pool.map(_job,jobs,chunksize=1):
                rows.append(row)
                if progress:progress(row)
    return rows


def compare_maxima(real,rows,*,scope='full'):
    out=[]
    for kind in ('iid','fixed_margins'):
        selected=[r[scope] for r in rows if r['null_model']==kind]
        if not selected:raise ValueError('Both null families required')
        for family in FAMILIES:
            a=np.array([r['maxima'][family] for r in selected]);obs=real['maxima'][family]
            p=(1+int((a>=obs).sum()))/(len(a)+1);correction=6 if family in PRIMARY else 3
            out.append(dict(scope=scope,null_model=kind,family=family,real_max=obs,
                null_median=float(np.median(a)),global_p=p,adjusted_p=min(1,correction*p),
                correction_families=correction,replicates=len(a),primary=family in PRIMARY))
    return out


def development_selection(x,comparison,*,leaders=None):
    x=research_matrix(x)
    if len(x)!=900:raise ValueError('Development selection requires exact1..900, no later data')
    passing=[]
    for f in PRIMARY:
        rows=[r for r in comparison if r['family']==f]
        if len(rows)==2 and {r['null_model'] for r in rows}=={'iid','fixed_margins'} and all(r['adjusted_p']<=.05 for r in rows):passing.append(f)
    raw=metric_vector(x);j=int(np.nanargmax(abs(raw['curve']['alpha']-.5)))
    eras=[]
    for a,b in ((0,300),(300,600),(600,900)):
        curve=dfa(raw['representations']['values'][a:b]);eras.append(dict(start=a+1,end=b,alpha=float(curve['alpha'][j]),r2=float(curve['r2'][j])))
    direction=np.sign(raw['curve']['alpha'][j]-.5)
    stable=all(np.sign(r['alpha']-.5)==direction and r['r2']>=.9 for r in eras)
    # A diagnostic series cannot borrow significance from another family/series.
    linked=[f for f in passing if leaders is not None
            and leaders.get(f,{}).get('series')==raw['representations']['names'][j]
            and (f!='persistent' or direction>0)
            and (f!='anti_persistent' or direction<0)]
    justified=bool(linked and stable)
    return dict(training_cutoff=900,training_hash=sha256(x.tobytes()).hexdigest(),later_start=901,
        selected_series=raw['representations']['names'][j],dfa_scales=raw['curve']['scales'].tolist(),
        detrending_order=1,rolling_windows=list(WINDOWS),crossover_boundaries=raw['cross']['boundaries'].tolist(),
        passing_primary_families=passing,linked_primary_families=linked,era_stable=stable,eras=eras,
        predictive_model_justified=justified,
        decision='REVIEW_PREDICTIVE_DESIGN' if justified else 'PREDICTIVE_MODEL_NOT_JUSTIFIED',
        ensemble_decision='NOT CURRENTLY JUSTIFIED',selection_rule='fixed declared scales; largest development absolute alpha deviation for diagnostics only')
