"""H14 fixed complexity vectors, independent calibration and own-max nulls."""
from hashlib import sha256
from math import ceil
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.complexity_encoding import representations,lz78,compression,temporal_shuffle
from src.analysis.entropy_complexity import (shannon,binary_block_entropy,conditional_entropy,
    permutation_entropy,sample_entropy)
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate

FAMILIES=('entropy','conditional','ordinal','lz','compression','chronological')
WINDOWS=(104,208,416)
COMPRESSORS=('zlib','bz2','lzma')
SCALARS=('sum','range','std','spacing_std')
GLOBALS=('full_binary','draw_packed','sorted_numbers','adjacent_gaps')


def rolling_endpoints(n,W):
    return sorted(set(range(W,n,104))|({n-1} if n-1>=W else set()))


def _measure(rep,kind,parameters):
    symbols=rep['symbols']
    if kind=='block_entropy':
        d=binary_block_entropy(symbols,parameters['L']);value=d['normalized'];direction=-1
    elif kind=='shannon':
        d=shannon(symbols,alphabet=rep['alphabet']);value=d['normalized'];direction=-1
    elif kind=='conditional_reduction':
        d=conditional_entropy(symbols,parameters['history']);value=d['reduction'];direction=1
    elif kind=='permutation_entropy':
        d=permutation_entropy(symbols,parameters['m'],parameters['tau']);value=d['normalized'];direction=-1
    elif kind=='sample_entropy':
        d=sample_entropy(symbols,parameters['m'],parameters['r']);value=d['entropy'];direction=-1
    elif kind=='lz78':
        d=lz78(symbols,rep['alphabet']);value=d['normalized'];direction=-1
    elif kind=='compression':
        d=compression(rep['data'],parameters['compressor'],symbol_count=len(symbols));value=d['ratio'];direction=-1
    else:raise ValueError('Unknown declared complexity metric')
    eligible=bool(d.get('eligible',True)) and value is not None and np.isfinite(value)
    return float(direction*value) if eligible else np.nan,value,d


def oriented_cell(x,spec):
    x=research_matrix(x);W=spec.get('window')
    if W is not None:
        if W not in WINDOWS or len(x)<W:raise ValueError('Selected rolling window requires sufficient prefix')
        x=x[-W:]
    rep=representations(x)[spec['representation']]
    params={key:spec[key] for key in ('L','history','m','tau','r','compressor') if key in spec}
    return _measure(rep,spec['kind'],params)[0]


def _whole_cells(x,*,subset=False):
    reps=representations(x);cells=[]
    def add(name,family,kind,**params):
        value,measurement,detail=_measure(reps[name],kind,params)
        cells.append((name,family,kind,params,value,measurement,detail))
    for name,rep in reps.items():
        binary=bool(rep['binary'])
        if binary:
            for L in ((3,) if subset else (1,2,3,4,5)):add(name,'entropy','block_entropy',L=L)
            for h in ((2,) if subset else (1,2)):add(name,'conditional','conditional_reduction',history=h)
        elif not subset and rep['alphabet'] is not None:add(name,'entropy','shannon')
        if name in SCALARS:
            for m in ((3,) if subset else (3,4,5)):
                for tau in ((1,) if subset else (1,2,4,8)):add(name,'ordinal','permutation_entropy',m=m,tau=tau)
            for m in ((2,) if subset else (2,3)):
                for r in ((.2,) if subset else (.15,.20,.25)):add(name,'ordinal','sample_entropy',m=m,r=r)
        if name not in SCALARS:add(name,'lz','lz78')
        if not subset or name in GLOBALS:
            for compressor in COMPRESSORS:add(name,'compression','compression',compressor=compressor)
    return cells


def _key(scope,name,kind,params,window=None,endpoint=None):
    p=','.join(f'{k}={v}' for k,v in sorted(params.items()))
    return '/'.join(str(v) for v in (scope,window,endpoint,name,kind,p) if v is not None)


def metric_vector(x,*,details=True):
    x=research_matrix(x)
    if len(x)<104:raise ValueError('H14 complete search needs at least104 completed draws')
    keys=[];values=[];families=[];metadata=[];rows=[];whole=_whole_cells(x)
    def append(scope,name,family,kind,params,value,measurement,detail,window=None,endpoint=None,base_family=None):
        key=_key(scope,name,kind,params,window,endpoint);keys.append(key);values.append(value);families.append(family)
        meta=dict(scope=scope,representation=name,family=family,kind=kind,**params)
        if window is not None:meta.update(window=window,endpoint=endpoint)
        if base_family is not None:meta['base_family']=base_family
        metadata.append(meta)
        if details:
            row=dict(key=key,**meta,oriented_value=float(value),measurement=measurement,eligible=bool(np.isfinite(value)))
            for k in ('samples','occupied','tie_fraction','A','B','std','radius','sparse','degenerate','phrases','symbols','raw_bytes','compressed_bytes','ratio','bits_per_symbol'):
                if k in detail and np.isscalar(detail[k]):row[k]=detail[k]
            rows.append(row)
    lookup={};cell_lookup={}
    for name,family,kind,params,value,measurement,detail in whole:
        append('whole',name,family,kind,params,value,measurement,detail)
        key=_key('whole',name,kind,params);lookup[key]=value
        cell_lookup[key]=(name,family,kind,params,value,measurement,detail)
    window_count=0
    for W in WINDOWS:
        for end in rolling_endpoints(len(x),W):
            window_count+=1;reps=representations(x[end-W:end])
            specs=[]
            for name in [f'number{n:02d}' for n in range(1,46)]:
                specs.extend([(name,'entropy','block_entropy',dict(L=3)),(name,'conditional','conditional_reduction',dict(history=1)),
                    (name,'lz','lz78',{})])
            specs.extend([('draw_packed','compression','compression',dict(compressor='zlib')),
                ('sum','ordinal','permutation_entropy',dict(m=3,tau=1)),('sum','ordinal','sample_entropy',dict(m=2,r=.2))])
            for name,family,kind,params in specs:
                value,measurement,detail=_measure(reps[name],kind,params)
                append('rolling',name,family,kind,params,value,measurement,detail,W,end)
    # All histories use their own exact draw contents and deterministic three
    # inner permutations. The outer 199 draw permutations are a separate test.
    reference=[];digest=int(sha256(x.tobytes()).hexdigest()[:8],16)
    for i in range(3):
        seed=int(np.random.SeedSequence([160003,digest,i]).generate_state(1)[0])
        cells=_whole_cells(temporal_shuffle(x,seed=seed),subset=True)
        reference.append({_key('whole',n,k,p):v for n,f,k,p,v,m,d in cells})
    for key,first in reference[0].items():
        base=[r[key] for r in reference];current=lookup[key]
        value=current-float(np.mean(base)) if np.isfinite([current,*base]).all() else np.nan
        # Resolve matching specification without relying on string parsing.
        cell=cell_lookup[key]
        name,family,kind,params,_,_,detail=cell
        append('chronological',name,'chronological',kind,params,value,value,{},base_family=family)
    family_counts={f:families.count(f) for f in FAMILIES}
    space=dict(representations=53,cells=len(keys),families=family_counts,rolling_windows=window_count,
        windows=list(WINDOWS),inner_permutations=3,chronological_cells=161)
    return dict(draws=len(x),keys=keys,values=np.array(values,float),families=families,metadata=metadata,rows=rows,
        space=space,representation_hash=sha256(x.tobytes()).hexdigest())


def fit_calibration(n,*,replicates=32,seed=160001,progress=None):
    if type(n) is not int or not 104<=n<=1245 or type(replicates) is not int or replicates<2:raise ValueError('Valid calibration scope and >=2 pilots required')
    vectors=[];layout=None;hashes=[]
    for i in range(replicates):
        child=int(np.random.SeedSequence([seed,n,i]).generate_state(1)[0]);r=metric_vector(iid_surrogate(n,seed=child),details=False)
        if layout is None:layout=r
        if r['keys']!=layout['keys']:raise RuntimeError('Pilot search-space mismatch')
        vectors.append(r['values']);hashes.append(r['representation_hash'])
        if progress:progress(f'Calibration N{n} {i+1}/{replicates}')
    matrix=np.array(vectors);valid=np.isfinite(matrix);count=valid.sum(0)
    mean=np.divide(np.where(valid,matrix,0).sum(0),count,out=np.zeros(matrix.shape[1]),where=count>0)
    squared=np.where(valid,(matrix-mean)**2,0).sum(0)
    std=np.sqrt(np.divide(squared,count-1,out=np.zeros_like(squared),where=count>1))
    eligible=(count>=ceil(.75*replicates))&(std>1e-12)
    return dict(draws=n,keys=layout['keys'],families=layout['families'],metadata=layout['metadata'],space=layout['space'],
        mean=mean,std=std,eligible=eligible,finite_count=count,pilot_values=matrix,pilot_hashes=hashes,replicates=replicates,seed=seed)


def standardize(raw,calibration):
    if raw['keys']!=calibration['keys']:raise ValueError('Frozen calibration key mismatch')
    values=np.asarray(raw['values']);mean=np.asarray(calibration['mean']);std=np.asarray(calibration['std'])
    eligible=np.asarray(calibration['eligible'])&np.isfinite(values)&(std>1e-12)
    return np.divide(values-mean,std,out=np.full(len(values),np.nan),where=eligible)


def complete_search(raw,calibration):
    z=standardize(raw,calibration);maxima={};leaders={}
    for family in FAMILIES:
        keep=np.array([f==family for f in raw['families']])&np.isfinite(z)
        if not keep.any():raise ValueError(f'No calibratable cells in family {family}')
        i=int(np.argmax(np.where(keep,z,-np.inf)));maxima[family]=float(z[i])
        leaders[family]=dict(index=i,key=raw['keys'][i],z=float(z[i]),oriented_value=float(raw['values'][i]),**raw['metadata'][i])
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],
        eligible_cells=int(np.isfinite(z).sum()),representation_hash=raw['representation_hash'])


def _null_job(job):
    x,kind,code,i,seed,calibrations,include_development=job;output=dict(null_model=kind,replicate=i,rebuilt=True)
    scopes=[('full',len(x),x)]+([('development',900,x[:900])] if include_development else [])
    for index,(scope,n,actual) in enumerate(scopes):
        child=int(np.random.SeedSequence([seed,code,i,index]).generate_state(1)[0])
        if kind=='iid':null=iid_surrogate(n,seed=child)
        elif kind=='fixed_margins':null=constrained_surrogate(actual,seed=child)
        else:null=temporal_shuffle(actual,seed=child)
        raw=metric_vector(null,details=False);r=complete_search(raw,calibrations[n])
        output[scope]=dict(r,seed=child,raw_values=raw['values'],changed_fraction=float((actual!=null).mean()))
    return output


def _initialize_worker(x,calibrations,include_development):
    global _WORKER_DATA
    _WORKER_DATA=(x,calibrations,include_development)


def _worker_job(job):
    kind,code,i,seed=job;x,calibrations,include_development=_WORKER_DATA
    return _null_job((x,kind,code,i,seed,calibrations,include_development))


def null_search(x,calibrations,*,replicates=199,seed=160042,workers=1,include_development=True,progress=None):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive null counts required')
    if include_development and len(x)!=1245:raise ValueError('Full+development study requires exact1..1245')
    # Pilot matrices are retained on disk, but workers only need frozen scales.
    calibrations={n:{k:cal[k] for k in ('keys','mean','std','eligible')} for n,cal in calibrations.items()}
    jobs=[(k,c,i,seed) for k,c in [('iid',0),('fixed_margins',1),('draw_shuffle',2)] for i in range(replicates)]
    rows=[]
    def consume(iterator):
        for row in iterator:
            rows.append(row)
            if progress:progress(row)
    if workers==1:consume(_null_job((x,k,c,i,s,calibrations,include_development)) for k,c,i,s in jobs)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers,initializer=_initialize_worker,
            initargs=(x,calibrations,include_development)) as pool:consume(pool.map(_worker_job,jobs))
    return rows


def compare_maxima(real,rows,*,scope):
    output=[]
    for kind in ('iid','fixed_margins','draw_shuffle'):
        group=[r[scope] for r in rows if r['null_model']==kind]
        if not group:raise ValueError('Three complete null families required')
        for family in FAMILIES:
            values=np.array([r['maxima'][family] for r in group]);observed=real['maxima'][family]
            exceed=int((values>=observed).sum());p=(1+exceed)/(len(values)+1)
            output.append(dict(scope=scope,cutoff=real['draws'],null_model=kind,family=family,real_max=observed,
                null_mean=float(values.mean()),null_q95=float(np.quantile(values,.95)),exceedances=exceed,
                replicates=len(values),global_p=p,adjusted_p=min(1.,6*p)))
    return output
