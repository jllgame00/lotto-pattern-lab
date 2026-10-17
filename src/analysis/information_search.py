"""H11 complete pair/configuration search; every surrogate chooses its own maxima."""
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.analysis.information import LAGS,HISTORIES,mi_matrix,te_matrix

FAMILIES=('mi','cmi','te','asymmetry','stable_te')


def search_space(lags=LAGS,histories=HISTORIES):
    pairs=45*44;configs=len(lags)*len(histories)
    return dict(numbers=45,directed_pairs=pairs,unordered_pairs=990,lags=list(lags),
        histories=[list(h) for h in histories],mi_cross=pairs*len(lags),self_mi=45*len(lags),
        cmi=pairs*len(lags),te=pairs*configs,asymmetry=990*configs,stable_te=pairs*configs,
        te_era_evaluations=3*pairs*configs,families=5)


def _configurations(lags,histories):
    if not lags or len(set(lags))!=len(lags) or any(lag not in LAGS for lag in lags):raise ValueError('Declared lag subset required')
    if not histories or len(set(histories))!=len(histories) or any(h not in HISTORIES for h in histories):raise ValueError('Declared small histories required')
    # CMI is always evaluated, even if an exploratory subset omits k1/l1.
    return [(lag,k,l) for lag in lags for k,l in dict.fromkeys(((1,1),*histories))]


def _best(matrix,eligible,**metadata):
    valid=np.asarray(eligible,bool)
    if valid.any():
        i,j=np.unravel_index(np.argmax(np.where(valid,matrix,-np.inf)),matrix.shape)
        value=float(matrix[i,j]);supported=True
    else:i,j=0,1;value=0.;supported=False
    return dict(source=int(i+1),target=int(j+1),value=value,eligible=supported,**metadata)


def stable_evidence(era_results):
    """Direction and support must persist in every era; negative MM minima score0."""
    if len(era_results)!=3:raise ValueError('Exactly three predeclared eras required')
    size=len(era_results[0]['raw']);mask=~np.eye(size,dtype=bool)
    for e in era_results:mask&=e['eligible']&e['eligible'].T&(e['raw']>e['raw'].T)
    score=np.maximum(0,np.minimum.reduce([e['corrected'] for e in era_results]))
    return np.where(mask,score,0.),mask


def complete_search(x,*,lags=LAGS,histories=HISTORIES,details=True):
    x=research_matrix(x)
    if len(x)<960:raise ValueError('At least960 draws for three supported historical eras')
    configs=_configurations(lags,histories);space=search_space(lags,histories)
    cross=~np.eye(45,dtype=bool);upper=np.triu(cross,1)
    eras=np.array_split(x,3);maxima=dict.fromkeys(FAMILIES,0.);leaders={}
    mi_rows=[];te_rows=[];arrays={};eligible_counts=dict.fromkeys(FAMILIES,0)
    def update(family,candidate):
        if family not in leaders or candidate['value']>maxima[family]:
            maxima[family]=candidate['value'];leaders[family]=candidate
    for lag in lags:
        result=mi_matrix(x,lag);mask=result['eligible']&cross
        candidate=_best(result['raw'],mask,lag=lag,k=0,l=1,samples=result['samples'])
        update('mi',candidate);eligible_counts['mi']+=int(mask.sum())
        if details:
            arrays[f'mi_lag{lag}_counts']=result['counts'];arrays[f'mi_lag{lag}_raw']=result['raw']
            arrays[f'mi_lag{lag}_corrected']=result['corrected'];arrays[f'mi_lag{lag}_eligible']=result['eligible']
            for i in range(45):
                for j in range(45):
                    mi_rows.append(dict(source=i+1,target=j+1,lag=lag,value=float(result['raw'][i,j]),
                        corrected=float(result['corrected'][i,j]),samples=result['samples'],
                        occupied=int(result['occupied'][i,j]),sparse=bool(result['sparse'][i,j]),
                        eligible=bool(result['eligible'][i,j]),self_reference=i==j))
    for lag,k,l in configs:
        full=te_matrix(x,lag,k,l);mask=full['eligible']&cross
        if (k,l)==(1,1):
            update('cmi',_best(full['raw'],mask,lag=lag,k=k,l=l,samples=full['samples']))
            eligible_counts['cmi']+=int(mask.sum())
        if (k,l) not in histories:continue
        update('te',_best(full['raw'],mask,lag=lag,k=k,l=l,samples=full['samples']))
        asym=full['raw']-full['raw'].T;amask=mask&mask.T&upper
        a=_best(np.abs(asym),amask,lag=lag,k=k,l=l,samples=full['samples'])
        i,j=a['source']-1,a['target']-1;a['signed_difference']=float(asym[i,j])
        a['forward']=float(full['raw'][i,j]);a['reverse']=float(full['raw'][j,i]);update('asymmetry',a)
        era_results=[te_matrix(era,lag,k,l) for era in eras]
        stability,stable_mask=stable_evidence(era_results)
        update('stable_te',_best(stability,stable_mask,lag=lag,k=k,l=l,
            era_samples=[int(e['samples']) for e in era_results]))
        eligible_counts['te']+=int(mask.sum());eligible_counts['asymmetry']+=int(amask.sum())
        eligible_counts['stable_te']+=int(stable_mask.sum())
        if details:
            key=f'te_lag{lag}_k{k}_l{l}'
            for field in ('counts','raw','corrected','eligible'):arrays[key+'_'+field]=full[field]
            for era,e in enumerate(era_results):
                arrays[key+f'_era{era}_raw']=e['raw'];arrays[key+f'_era{era}_corrected']=e['corrected']
                arrays[key+f'_era{era}_eligible']=e['eligible']
            for i,j in zip(*np.where(cross)):
                te_rows.append(dict(source=int(i+1),target=int(j+1),lag=lag,k=k,l=l,
                    value=float(full['raw'][i,j]),corrected=float(full['corrected'][i,j]),
                    reverse=float(full['raw'][j,i]),directional_difference=float(asym[i,j]),
                    samples=full['samples'],occupied=int(full['occupied'][i,j]),sparse=bool(full['sparse'][i,j]),
                    eligible=bool(full['eligible'][i,j]),stable_score=float(stability[i,j]) if stable_mask[i,j] else 0.,
                    stable_eligible=bool(stable_mask[i,j])))
    return dict(maxima=maxima,leaders=leaders,space=space,eligible_counts=eligible_counts,
        mi_rows=mi_rows,te_rows=te_rows,arrays=arrays,representation_hash=sha256(x.tobytes()).hexdigest(),
        eras=[[1,len(eras[0])],[len(eras[0])+1,len(eras[0])+len(eras[1])],[len(x)-len(eras[2])+1,len(x)]])


def _null_job(job):
    x,kind,code,i,seed,args=job
    child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
    null=iid_surrogate(len(x),seed=child) if code==0 else constrained_surrogate(x,seed=child)
    result=complete_search(null,details=False,**args)
    return dict(null_model=kind,replicate=i,seed=child,rebuilt=True,space=result['space'],
        eligible_counts=result['eligible_counts'],representation_hash=result['representation_hash'],
        changed_fraction=float((x!=null).mean()),**result['maxima'])


def null_search(x,*,replicates=199,seed=130042,search_args=None,workers=1,progress=None):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    jobs=[(x,k,c,i,seed,search_args or {}) for k,c in [('iid',0),('fixed_margins',1)] for i in range(replicates)]
    rows=[]
    def consume(iterator):
        for row in iterator:
            rows.append(row)
            if progress:progress(row)
    if workers==1:consume(map(_null_job,jobs))
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers) as pool:consume(pool.map(_null_job,jobs))
    return rows


def compare_maxima(real,rows):
    output=[]
    for kind in ('iid','fixed_margins'):
        group=[r for r in rows if r['null_model']==kind]
        if not group:raise ValueError('Both null families required')
        for family in FAMILIES:
            values=np.array([r[family] for r in group]);observed=real['maxima'][family]
            exceed=int((values>=observed).sum());p=(1+exceed)/(len(values)+1)
            output.append(dict(null_model=kind,family=family,real_max=observed,null_mean=float(values.mean()),
                null_q95=float(np.quantile(values,.95)),exceedances=exceed,replicates=len(values),
                global_p=p,adjusted_p=min(1.,5*p)))
    return output


def shifted_sources(x,*,replicates=19,seed=130043):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or len(x)<108:raise ValueError('Nontrivial circular shift unavailable')
    rng=np.random.default_rng(seed);output=[]
    for _ in range(replicates):
        offsets=rng.integers(53,len(x)-52,size=45)
        index=(np.arange(len(x))[:,None]-offsets[None,:])%len(x)
        output.append(np.take_along_axis(x,index,axis=0))
    return output


def temporal_randomization(x,*,replicates=19,seed=130043,lags=LAGS,histories=HISTORIES):
    """Auxiliary relation-specific source null, not a valid six-per-row history."""
    x=research_matrix(x);_configurations(lags,histories)
    mi_null=[];te_null=[]
    for source in shifted_sources(x,replicates=replicates,seed=seed):
        mi_null.append([np.where((r:=mi_matrix(x,lag,source=source))['eligible'],r['raw'],np.nan) for lag in lags])
        te_null.append([np.where((r:=te_matrix(x,lag,k,l,source=source))['eligible'],r['raw'],np.nan)
            for lag in lags for k,l in histories])
    return dict(replicates=replicates,seed=seed,mi_null=np.asarray(mi_null),te_null=np.asarray(te_null),
        lags=list(lags),histories=[list(h) for h in histories],target_history_unchanged=True)
