"""Frozen H21 search: every Lotto surrogate fits its own complete spectrum."""
from concurrent.futures import ProcessPoolExecutor
from hashlib import sha256
import numpy as np
from .recurrence import research_matrix
from .spatiotemporal import iid_surrogate,constrained_surrogate
from .random_matrix import (WINDOWS,RANKS,LAGS,fit_matrix,rolling_endpoints,
                            subspace_comparison,lagged_spectrum)

FAMILIES=('largest','smallest','localization','concentration','stability','lagged_secondary')
RECURRENCE_STEPS=(1,2,4)


def _padded(values):
    out=np.full(44,np.nan);out[:len(values)]=values;return out


def metric_vector(x,*,details=True):
    x=research_matrix(x);n=len(x)
    if n<312:raise ValueError('RMT complete search requires312..1245 historical draws')
    intervals=[]
    def interval(location,start,end,window=0):
        local=x[start-1:end]
        corr=fit_matrix(local);cov=fit_matrix(local,kind='covariance')
        if len(local)<2*corr['nontrivial_dimension']:
            raise ValueError('Insufficient sample-to-dimension ratio')
        row=dict(location=location,start=start,end=end,window=window,correlation=corr,covariance=cov)
        intervals.append(row);return row
    whole=interval('whole',1,n)
    rolling=[]
    for window in WINDOWS:
        if window>n:continue
        for end in rolling_endpoints(n,window):rolling.append(interval('rolling',int(end-window+1),int(end),window))
    edges=np.linspace(0,n,4,dtype=int)
    eras=[interval(f'era{i+1}',int(edges[i]+1),int(edges[i+1])) for i in range(3)]
    keys=[];families=[];metadata=[];values=[];stability=[]
    def add(family,key,value,**meta):
        keys.append(f'{family}|{key}');families.append(family)
        metadata.append(dict(family=family,**meta));values.append(float(value))
    for row in [whole]+rolling:
        fit=row['correlation'];a=fit['eigenvalues'];key=f"{row['location']}|{row['window']}|{row['end']}"
        meta={k:row[k] for k in ('location','start','end','window')}
        add('largest',key,a[0] if len(a) else np.nan,**meta)
        add('smallest',key,-a[-1] if len(a)==44 else np.nan,**meta)
        for j in range(44):add('localization',f'{key}|{j+1}',fit['ipr'][j] if j<len(a) else np.nan,mode=j+1,**meta)
        if row['location']=='rolling':
            for r in RANKS:add('concentration',f'{key}|{r}',a[:r].sum()/fit['trace'] if len(a)>=r and fit['trace']>0 else np.nan,rank=r,**meta)
    def compare(a,b,label,**extra):
        results={}
        for r in RANKS:
            af=a['correlation'];bf=b['correlation']
            if min(af['nontrivial_dimension'],bf['nontrivial_dimension'])<r:
                score=np.nan;diagnostic=dict(principal_angles=np.full(r,np.nan),projection_distance=np.nan,aligned_leading_correlation=np.nan)
            else:
                diagnostic=subspace_comparison(af['eigenvectors'],bf['eigenvectors'],r)
                score=diagnostic['overlap']
            info=dict(location=label,rank=r,start=a['start'],end=b['end'],first_end=a['end'],second_start=b['start'],**extra)
            key='|'.join(map(str,(label,extra.get('window',0),a['end'],b['end'],r)))
            add('stability',key,score,**info)
            stability.append(dict(info,overlap=score,**{k:diagnostic[k] for k in ('principal_angles','projection_distance','aligned_leading_correlation')}))
            results[r]=score
        return results
    for window in WINDOWS:
        rows=[a for a in rolling if a['window']==window]
        for k in RECURRENCE_STEPS:
            for i in range(max(0,len(rows)-k)):compare(rows[i],rows[i+k],'rolling_pair',window=window,step=k)
    era_comparisons=[compare(eras[a],eras[b],'era_pair',era_pair=f'{a+1}_{b+1}') for a,b in ((0,1),(1,2),(0,2))]
    for r in RANKS:
        scores=[a[r] for a in era_comparisons]
        add('stability',f'era_min|{r}',min(scores) if np.isfinite(scores).all() else np.nan,location='era_min',rank=r,start=1,end=n)
    lagged=[]
    for lag in LAGS:
        row=lagged_spectrum(x,lag);lagged.append(row);s=row['singular_values']
        add('lagged_secondary',f'{lag}|largest',s[0] if len(s) else np.nan,location='lagged',lag=lag,statistic='largest_sv')
        for i,r in enumerate(RANKS):add('lagged_secondary',f'{lag}|concentration|{r}',row['squared_concentration'][i],location='lagged',lag=lag,statistic='concentration',rank=r)
        for side in ('left','right'):
            for j in range(5):add('lagged_secondary',f'{lag}|{side}_ipr|{j+1}',row[f'{side}_ipr'][j] if j<len(s) else np.nan,location='lagged',lag=lag,statistic=f'{side}_ipr',mode=j+1)
    space=dict(cells=len(keys),numbers=45,primary_representation='correlation',secondary_representation='covariance',
        structural_mode='std for correlation; ones on active covariance coordinates',
        windows=list(WINDOWS),stride=104,ranks=list(RANKS),recurrence_steps=list(RECURRENCE_STEPS),
        lags=list(LAGS),lag_scope='whole only',rolling_fits=len(rolling),era_fits=3,
        family_cells={f:families.count(f) for f in FAMILIES})
    spectra=np.array([[_padded(row[k]['eigenvalues']) for k in ('correlation','covariance')] for row in intervals])
    raw=dict(draws=n,keys=keys,families=families,metadata=metadata,values=np.array(values),space=space,
             representation_hash=sha256(x.tobytes()).hexdigest(),spectra=spectra)
    if details:raw.update(intervals=intervals,stability=stability,lagged=lagged)
    return raw


def fit_calibration(n,*,replicates=32,seed=221001,progress=None):
    if type(n) is not int or not 312<=n<=1245 or type(replicates) is not int or replicates<4:
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
    active=np.asarray(c['eligible'])&np.isfinite(raw['values']);out=np.full(len(raw['keys']),np.nan)
    out[active]=(raw['values'][active]-np.asarray(c['mean'])[active])/np.asarray(c['std'])[active]
    return out


def complete_search(raw,c):
    z=standardize(raw,c);families=np.array(raw['families']);maxima={};leaders={}
    for family in FAMILIES:
        active=np.flatnonzero((families==family)&np.isfinite(z))
        if not len(active):raise ValueError(f'Unsupported family {family}')
        i=int(active[np.argmax(z[active])]);maxima[family]=float(z[i])
        leaders[family]=dict(index=i,key=raw['keys'][i],value=float(raw['values'][i]),z=float(z[i]),**raw['metadata'][i])
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],eligible_cells=int(np.isfinite(z).sum()),representation_hash=raw['representation_hash'])


def _null_job(x,c,kind,code,i,seed,dev):
    row=dict(null_model=kind,replicate=i)
    for scope,n,actual in [('full',len(x),x)]+([('development',900,x[:900])] if dev else []):
        child=int(np.random.SeedSequence([seed,code,i,n]).generate_state(1)[0])
        null=iid_surrogate(n,seed=child) if kind=='iid' else constrained_surrogate(actual,seed=child)
        raw=metric_vector(null,details=False)
        row[scope]=dict(complete_search(raw,c[n]),seed=child,rebuilt=True,raw_values=raw['values'],spectra=raw['spectra'],
            changed_fraction=float((actual!=null).mean()),row_six=bool((null.sum(1)==6).all()),
            fixed_margins_preserved=bool(np.array_equal(actual.sum(0),null.sum(0))) if kind!='iid' else None)
    return row


def _initialize(x,c,dev):
    global _WORKER
    _WORKER=x,c,dev


def _job(job):
    x,c,dev=_WORKER;return _null_job(x,c,*job,dev)


def null_search(x,calibrations,*,replicates=199,seed=220042,workers=1,include_development=True,progress=None):
    x=research_matrix(x)
    if include_development and len(x)!=1245:raise ValueError('Full+development requires exact1..1245')
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    c={n:{k:v[k] for k in ('draws','keys','mean','std','eligible')} for n,v in calibrations.items()}
    jobs=[(kind,code,i,seed) for kind,code in [('iid',0),('fixed_margins',1)] for i in range(replicates)]
    rows=[]
    def collect(iterator):
        for row in iterator:
            rows.append(row)
            if progress:progress(row)
    if workers==1:collect(_null_job(x,c,*job,include_development) for job in jobs)
    else:
        with ProcessPoolExecutor(max_workers=workers,initializer=_initialize,initargs=(x,c,include_development)) as pool:
            collect(pool.map(_job,jobs,chunksize=1))
    return rows


def compare_maxima(real,rows,*,scope='full'):
    out=[]
    for kind in ('iid','fixed_margins'):
        selected=[r[scope] for r in rows if r['null_model']==kind]
        if not selected:raise ValueError('Both nulls required')
        for family in FAMILIES:
            a=np.array([r['maxima'][family] for r in selected]);value=real['maxima'][family]
            p=(1+int((a>=value).sum()))/(len(a)+1)
            out.append(dict(scope=scope,null_model=kind,family=family,real_max=value,null_median=float(np.median(a)),
                global_p=p,adjusted_p=min(1.,6*p),replicates=len(a),primary=family!='lagged_secondary'))
    return out


def development_selection(x,c,rows):
    x=research_matrix(x)
    if len(x)!=900 or c['draws']!=900:raise ValueError('Development requires exact1..900')
    raw=metric_vector(x);z=standardize(raw,c)
    tests=[]
    def cell_test(key,family):
        i=raw['keys'].index(key);pair=[]
        for kind in ('iid','fixed_margins'):
            a=np.array([row['development']['maxima'][family] for row in rows if row['null_model']==kind])
            if not len(a):raise ValueError('Both development null families required')
            p=(1+int((a>=z[i]).sum()))/(len(a)+1) if np.isfinite(z[i]) else 1.
            test=dict(key=key,family=family,null_model=kind,z=float(z[i]),global_p=p,adjusted_p=min(1.,6*p))
            tests.append(test);pair.append(test)
        return all(t['adjusted_p']<=.05 for t in pair)
    spectral=cell_test('largest|whole|0|900','largest')
    stable=[r for r in RANKS if cell_test(f'stability|era_min|{r}','stability')]
    justified=bool(spectral and stable)
    return dict(training_cutoff=900,training_hash=sha256(x.tobytes()).hexdigest(),later_start=901,
        whole_leading_mode_passed=spectral,stable_ranks=stable,gate_tests=tests,
        predictive_model_justified=justified,decision='REVIEW_PREDICTIVE_DESIGN' if justified else 'PREDICTIVE_MODEL_NOT_JUSTIFIED',
        ensemble_decision='NOT CURRENTLY JUSTIFIED',primary_representation='correlation',windows=list(WINDOWS),ranks=list(RANKS),
        rule='same whole leading-mode cell and one same-rank nonoverlap-era-min cell vs own family global null maxima, both nulls, Bonferroni6')
