"""H13 complete own-maximum transformed searches on valid Lotto histories."""
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.modular_space import MODULI,LAGS,representation as modular_representation,transition
from src.analysis.difference_space import representation as difference_representation,absolute_relation,shape_successor
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate

FAMILIES=('modular_structure','modular_temporal','modular_successor','distance','shape')


def correlation(a,b,*,columns=False):
    a=np.asarray(a,float);b=np.asarray(b,float)
    a=a-a.mean(axis=0 if columns else None);b=b-b.mean(axis=0 if columns else None)
    a=a.ravel();b=b.ravel();denom=np.linalg.norm(a)*np.linalg.norm(b)
    return float(a@b/denom) if denom>1e-12 else 0.


def complete_search(x,*,details=True):
    x=research_matrix(x)
    if len(x)<104:raise ValueError('Complete H13 search needs at least104 completed draws')
    maxima=dict.fromkeys(FAMILIES,0.);leaders={};arrays={};mod_rows=[];temporal_rows=[];successor_rows=[];distance_rows=[];shape_rows=[]
    eligible_successor=0
    def update(family,value,**metadata):
        if family not in leaders or value>maxima[family]:
            maxima[family]=float(value);leaders[family]=dict(value=float(value),**metadata)
    for k in MODULI:
        r=modular_representation(x,k);H=r['histogram'];variance=np.diag(r['covariance'])
        z=(H.sum(0)-len(x)*r['expected'])/np.sqrt(len(x)*variance)
        for residue in range(k):
            update('modular_structure',abs(z[residue]),modulus=k,residue=residue,signed_z=float(z[residue]),
                count=int(H[:,residue].sum()),expected=float(len(x)*r['expected'][residue]))
            if details:mod_rows.append(dict(modulus=k,residue=residue,count=int(H[:,residue].sum()),
                expected=float(len(x)*r['expected'][residue]),z=float(z[residue]),population=int(r['populations'][residue])))
        if details:
            for key in ('histogram','populations','expected','covariance','occupied','concentration','entropy','repeats','repeated_classes','imbalance'):
                arrays[f'mod{k}_{key}']=r[key]
        for lag in LAGS:
            for feature,series in [('histogram',H),('concentration',r['concentration']),('entropy',r['entropy'])]:
                c=correlation(series[:-lag],series[lag:],columns=feature=='histogram')
                update('modular_temporal',abs(c),modulus=k,lag=lag,feature=feature,signed_correlation=c)
                if details:temporal_rows.append(dict(modulus=k,lag=lag,feature=feature,correlation=c))
            t=transition(x,k,lag);mask=t['eligible'];eligible_successor+=int(mask.sum())
            values=np.where(mask,np.abs(t['z']),0.);a,b=np.unravel_index(values.argmax(),values.shape)
            update('modular_successor',values[a,b],modulus=k,lag=lag,residue=int(a),source_count=int(b),
                support=int(t['counts'][a,b]),conditional_mean=float(t['conditional_means'][a,b]) if mask[a,b] else None,
                baseline=float(t['baseline'][a]),eligible=bool(mask[a,b]))
            if details:
                for key in ('counts','sums','conditional_means','baseline','variance','z','eligible'):arrays[f'mod{k}_lag{lag}_{key}']=t[key]
                for residue,state in np.ndindex(k,7):
                    successor_rows.append(dict(modulus=k,lag=lag,residue=residue,source_count=state,
                        support=int(t['counts'][residue,state]),eligible=bool(mask[residue,state]),
                        conditional_mean=float(t['conditional_means'][residue,state]),baseline=float(t['baseline'][residue]),
                        z=float(t['z'][residue,state])))
    d=difference_representation(x)
    if details:
        for key,value in d.items():arrays[f'difference_{key}']=value
    for lag in LAGS:
        t=absolute_relation(x,lag)
        for distance in range(1,45):
            update('distance',abs(t['z'][distance]),lag=lag,distance=distance,signed_z=float(t['z'][distance]),
                observed=float(t['observed'][distance]),expected=float(t['expected'][distance]),opportunity=float(t['opportunity'][distance]))
            if details:distance_rows.append(dict(lag=lag,distance=distance,observed=float(t['observed'][distance]),
                expected=float(t['expected'][distance]),opportunity=float(t['opportunity'][distance]),z=float(t['z'][distance])))
        if details:
            for key in ('observed','opportunity','expected','variance','z'):arrays[f'distance_lag{lag}_{key}']=t[key]
        c=correlation(d['normalized_gaps'][:-lag],d['normalized_gaps'][lag:],columns=True)
        update('shape',abs(c)*np.sqrt(len(x)-lag),kind='lag_correlation',lag=lag,signed_correlation=c)
    for K in (10,25):
        s=shape_successor(x,K)
        update('shape',max(0.,s['score']),kind='causal_successor_gain',K=K,queries=len(s['rows']))
        if details:
            shape_rows.extend(s['rows'])
            for key in ('predictions','baseline_predictions','actual','gains'):arrays[f'shape_K{K}_{key}']=s[key]
    space=dict(numbers=45,moduli=list(MODULI),lags=list(LAGS),modular_structure_cells=27,
        modular_temporal_cells=126,modular_successor_cells=1323,distance_cells=308,shape_cells=9,
        primary_cells=1793,families=5,shape_K=[10,25],successor_support=20)
    return dict(maxima=maxima,leaders=leaders,space=space,eligible_successor_cells=eligible_successor,
        representation_hash=sha256(x.tobytes()).hexdigest(),arrays=arrays,modular_rows=mod_rows,
        temporal_rows=temporal_rows,successor_rows=successor_rows,distance_rows=distance_rows,shape_rows=shape_rows)


def _null_job(job):
    x,kind,code,i,seed=job;child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
    surrogate=iid_surrogate(len(x),seed=child) if code==0 else constrained_surrogate(x,seed=child)
    r=complete_search(surrogate,details=False)
    return dict(null_model=kind,replicate=i,seed=child,rebuilt=True,space=r['space'],
        maxima=r['maxima'],eligible_successor_cells=r['eligible_successor_cells'],representation_hash=r['representation_hash'],
        changed_fraction=float((x!=surrogate).mean()))


def null_search(x,*,replicates=199,seed=150042,workers=1,progress=None):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    jobs=[(x,kind,code,i,seed) for kind,code in [('iid',0),('fixed_margins',1)] for i in range(replicates)];rows=[]
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
            values=np.array([r['maxima'][family] for r in group]);observed=real['maxima'][family]
            exceed=int((values>=observed).sum());p=(1+exceed)/(len(values)+1)
            output.append(dict(null_model=kind,family=family,real_max=observed,null_mean=float(values.mean()),
                null_q95=float(np.quantile(values,.95)),exceedances=exceed,replicates=len(values),global_p=p,adjusted_p=min(1.,5*p)))
    return output
