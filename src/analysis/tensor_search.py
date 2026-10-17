"""H15 predeclared 165-cell search; independent calibration and own-max nulls."""
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import iid_surrogate, constrained_surrogate
from src.analysis.tensor_representation import build_tensors
from src.analysis.tensor_decomposition import hosvd, effective_rank, subspace_similarity

FAMILIES=('concentration','reconstruction','effective_rank','stability','temporal')
NUMBER_RANKS=(2,3,4,6)
FEATURE_RANKS=(1,2,3)
MAX_RANKS=(8,6,3)


def temporal_correlation(series):
    series=np.asarray(series,dtype=float)
    a,b=series[:-1],series[1:]
    if len(a)<2 or np.std(a)<1e-12 or np.std(b)<1e-12:return float('nan')
    return float(abs(np.corrcoef(a,b)[0,1]))


def _identifiable(fit,shape,mode,rank):
    spectrum=fit['singular_values'][mode]
    tolerance=max(shape[mode],int(np.prod(shape)//shape[mode]))*np.finfo(float).eps*spectrum[0]
    return bool(spectrum[rank-1]>tolerance)


def metric_vector(x,*,details=True):
    x=research_matrix(x)
    if len(x)<104:raise ValueError('H15 complete search requires at least104 completed draws')
    tensors=build_tensors(x);keys=[];values=[];families=[];metadata=[];rows=[]
    def add(name,family,kind,value,**parameters):
        key='/'.join((name,kind,','.join(f'{k}={v}' for k,v in sorted(parameters.items()))))
        meta=dict(tensor=name,family=family,kind=kind,**parameters)
        keys.append(key);families.append(family);values.append(float(value));metadata.append(meta)
        if details:rows.append(dict(key=key,**meta,oriented_value=float(value)))
    block_boundaries={}
    for name,rep in tensors.items():
        tensor=rep['values'];fit=hosvd(tensor,MAX_RANKS)
        for mode,ranks in enumerate(((1,2,4,8),(1,2,3,4,6),(1,2,3))):
            spectrum=fit['singular_values'][mode];energy=spectrum**2;total=energy.sum()
            for rank in ranks:add(name,'concentration','mode_energy',float(energy[:rank].sum()/total),mode=mode,rank=rank)
            # Oriented upward: a smaller effective rank is stronger evidence.
            add(name,'effective_rank','effective_rank_fraction',-effective_rank(spectrum)/min(tensor.shape[mode],int(np.prod(tensor.shape)//tensor.shape[mode])),mode=mode)
        total=float(np.square(tensor).sum())
        for rn in NUMBER_RANKS:
            for rf in FEATURE_RANKS:
                retained=float(np.square(fit['core'][:8,:rn,:rf]).sum())/total
                add(name,'reconstruction','negative_relative_error',-float(np.sqrt(max(0.,1-retained))),time_rank=8,number_rank=rn,feature_rank=rf)
        blocks=np.array_split(np.arange(len(tensor)),3)
        block_boundaries[name]=[[int(rep['draws'][b[0]]),int(rep['draws'][b[-1]])] for b in blocks]
        fits=[hosvd(tensor[b],MAX_RANKS) for b in blocks]
        for rn in NUMBER_RANKS:
            for i,j in ((0,1),(0,2),(1,2)):
                valid=all(_identifiable(fits[k],tensor[blocks[k]].shape,1,rn) for k in (i,j))
                score=subspace_similarity(fits[i]['factors'][1][:,:rn],fits[j]['factors'][1][:,:rn]) if valid else np.nan
                add(name,'stability','number_subspace',score,number_rank=rn,block_a=i,block_b=j)
        for scope,block_fit,shape in [('whole',fit,tensor.shape)]+[(f'block{i}',f,tensor[blocks[i]].shape) for i,f in enumerate(fits)]:
            for component in range(4):
                score=temporal_correlation(block_fit['factors'][0][:,component]) if _identifiable(block_fit,shape,0,component+1) else np.nan
                add(name,'temporal','abs_lag1_correlation',score,scope=scope,component=component)
    counts={f:families.count(f) for f in FAMILIES}
    return dict(draws=len(x),keys=keys,values=np.array(values),families=families,metadata=metadata,rows=rows,
        dimensions={name:list(rep['values'].shape) for name,rep in tensors.items()},block_boundaries=block_boundaries,
        representation_hash=sha256(x.tobytes()).hexdigest(),
        space=dict(cells=len(keys),family_cells=counts,tensor_families=3,tucker_configurations=36,blocks_per_tensor=3))


def fit_calibration(n,*,replicates=32,seed=171001,progress=None):
    if type(replicates) is not int or replicates<4:raise ValueError('At least4 independent pilot histories required')
    if type(n) is not int or not 104<=n<=1245:raise ValueError('Historical calibration cutoff104..1245 only')
    vectors=[];raw=None
    for i in range(replicates):
        child=int(np.random.SeedSequence([seed,n,i]).generate_state(1)[0])
        raw=metric_vector(iid_surrogate(n,seed=child),details=False);vectors.append(raw['values'])
        if progress:progress(f'Calibration {n}: {i+1}/{replicates}')
    matrix=np.array(vectors);finite=np.isfinite(matrix).sum(axis=0)
    mean=np.nanmean(matrix,axis=0);std=np.nanstd(matrix,axis=0,ddof=1)
    eligible=(finite>=max(4,int(np.ceil(.75*replicates))))&(std>1e-12)
    return dict(keys=raw['keys'],families=raw['families'],metadata=raw['metadata'],mean=mean,std=std,eligible=eligible,
        finite_count=finite,pilot_values=matrix,replicates=replicates,seed=seed,draws=n,space=raw['space'])


def standardize(raw,calibration):
    if 'draws' in calibration and raw['draws']!=calibration['draws']:raise ValueError('Calibration cutoff mismatch')
    if raw['keys']!=calibration['keys']:raise ValueError('Calibration search-space identity mismatch')
    z=np.full(len(raw['keys']),np.nan);mask=np.asarray(calibration['eligible'],dtype=bool)&np.isfinite(raw['values'])
    z[mask]=(raw['values'][mask]-np.asarray(calibration['mean'])[mask])/np.asarray(calibration['std'])[mask]
    return z


def complete_search(raw,calibration):
    z=standardize(raw,calibration);maxima={};leaders={}
    for family in FAMILIES:
        choices=np.flatnonzero((np.array(raw['families'])==family)&np.isfinite(z))
        if not len(choices):raise ValueError(f'No eligible {family} search cell')
        index=int(choices[np.argmax(z[choices])]);maxima[family]=float(z[index])
        leaders[family]=dict(key=raw['keys'][index],z=float(z[index]),oriented_value=float(raw['values'][index]),**raw['metadata'][index])
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],
        dimensions=raw.get('dimensions'),block_boundaries=raw.get('block_boundaries'),
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


def null_search(x,calibrations,*,replicates=199,seed=170042,workers=1,include_development=True,progress=None):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive null counts required')
    if include_development and len(x)!=1245:raise ValueError('Full+development search requires exact1..1245')
    calibrations={n:{k:c[k] for k in ('keys','mean','std','eligible','draws')} for n,c in calibrations.items()}
    jobs=[(kind,code,i,seed) for kind,code in [('iid',0),('fixed_margins',1)] for i in range(replicates)]
    rows=[]
    def consume(iterator):
        for row in iterator:
            rows.append(row)
            if progress:progress(row)
    if workers==1:consume(_null_job(x,calibrations,*job,include_development) for job in jobs)
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers,initializer=_initialize_worker,initargs=(x,calibrations,include_development)) as pool:
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
                replicates=len(null),global_p=p,adjusted_p=min(1.,5*p)))
    return output


def choose_development(raw,z):
    if raw['draws']!=900:raise ValueError('Selection must use development1..900 only')
    z=np.asarray(z);valid=np.isfinite(z)
    if z.shape!=raw['values'].shape or not valid.any():raise ValueError('Invalid development search scores')
    selected=int(np.flatnonzero(valid)[np.argmax(z[valid])])
    return dict(cutoff=900,later_start=901,key=raw['keys'][selected],z=float(z[selected]),spec=dict(raw['metadata'][selected]))


def development_gate(rows,*,cutoff):
    if cutoff!=900:raise ValueError('Only development cutoff900 may determine predictive eligibility')
    table={(r['null_model'],r['family']):r['adjusted_p'] for r in rows}
    if len(rows)!=10 or set(table)!={(n,f) for n in ('iid','fixed_margins') for f in FAMILIES}:raise ValueError('Complete development comparisons required')
    structural=any(all(table[n,f]<=.05 for n in ('iid','fixed_margins')) for f in FAMILIES if f!='stability')
    stable=all(table[n,'stability']<=.05 for n in ('iid','fixed_margins'))
    # This is a prerequisite, never a claim that a forecast model is already justified.
    return dict(structure_supported=structural,stability_supported=stable,
        forecast_review_eligible=structural and stable,predictive_model_justified=False,
        status='FORECAST_REVIEW_REQUIRED' if structural and stable else 'PREDICTIVE_MODEL_NOT_JUSTIFIED')
