"""H18 fixed-grid segmentation search with independent own-max nulls."""
from functools import lru_cache
from hashlib import sha256
from itertools import combinations
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.analysis.change_point import segment,best_split,cusum,distribution_distance,boundary_concordance
from src.analysis.change_point_representation import build_contexts,shape_vector,MINIMUMS,MULTIPLIERS

FAMILIES=('single_number','global_shift','concentration','concordance','stability')
GLOBAL_UNITS=('A','B13','B26','B52','C')
UNITS=tuple(f'number{n:02d}' for n in range(1,46))+GLOBAL_UNITS
TOLERANCES=(13,26)


def configurations():
    return [(f'm{minimum}_p{multiplier}',minimum,multiplier) for minimum in MINIMUMS for multiplier in MULTIPLIERS]


def prefix_sizes(n):
    if type(n) is not int or not 520<=n<=1245:raise ValueError('Complete H18 search requires520..1245 draws')
    return [800,900,1000,1100,1245] if n==1245 else [n-400,n-300,n-200,n-100,n]


@lru_cache(maxsize=6)
def _fit_cached(raw,shape):
    x=np.frombuffer(raw,dtype=np.bool_).reshape(shape);contexts=build_contexts(x);fits={};inventory={}
    proposals={}
    for name,context in contexts.items():
        if name=='number':continue
        for minimum in MINIMUMS:proposals[name,minimum]=best_split(context['costs'],context['endpoints'],minimum=minimum)
    for minimum in MINIMUMS:proposals['number',minimum]=best_split(contexts['number']['costs'],contexts['number']['endpoints'],minimum=minimum)
    for key,minimum,multiplier in configurations():
        here={};edges=0;states=0
        for representation in ('number',*GLOBAL_UNITS):
            context=contexts[representation];endpoints=context['endpoints'];costs=context['costs']
            penalty=float(multiplier*context['dimension']*np.log(context['observations']))
            results=segment(costs,endpoints,minimum=minimum,penalty=penalty)
            index={int(v):i for i,v in enumerate(endpoints)}
            edges+=int(((endpoints[None,:]-endpoints[:,None])>=minimum).sum())*len(results)
            states+=len(endpoints)*len(results)
            for j,result in enumerate(results):
                unit=f'number{j+1:02d}' if representation=='number' else representation
                local=costs[:,:,j] if representation=='number' else costs
                boundaries=list(result['boundaries']);segments=result['segments'];gains=[]
                for k,b in enumerate(boundaries):
                    start,end=segments[k][0],segments[k+1][1]
                    gains.append(float(max(0.,local[index[start],index[end]]-local[index[start],index[b]]-local[index[b],index[end]])))
                proposal=proposals[representation,minimum][j]
                proposed=int(proposal['boundary']) if proposal['boundary'] is not None and proposal['gain']>1e-10 else None
                here[unit]=dict(result,minimum=minimum,multiplier=multiplier,penalty=penalty,representation=representation,
                    observations=context['observations'],used_draws=context['used_draws'],discarded_tail=context['discarded_tail'],
                    boundary_gains=gains,proposal_boundary=proposed,proposal_gain=float(proposal['gain']) if proposed is not None else 0.)
        fits[key]=here;inventory[key]=dict(dp_state_units=states,admissible_segment_transitions=edges)
    return dict(fits=fits,inventory=inventory,context_sizes={name:dict(observations=c['observations'],endpoints=len(c['endpoints']),
        dimension=c['dimension'],used_draws=c['used_draws'],discarded_tail=c['discarded_tail']) for name,c in contexts.items()})


def fit_prefix(x):
    x=research_matrix(x)
    return _fit_cached(x.tobytes(),x.shape)


def _boundaries(fit,kind):
    return fit['boundaries'] if kind=='detected' else ([fit['proposal_boundary']] if fit['proposal_boundary'] is not None else [])


def stable_boundary(full,earlier,*,tolerance,kind):
    if kind not in ('detected','proposal') or tolerance not in TOLERANCES:raise ValueError('Predeclared stability definition required')
    best=dict(score=0.,boundary=None,matches=0,eligible_prefixes=0)
    candidates=_boundaries(full,kind)
    for j,boundary in enumerate(candidates):
        eligible=[p for p in earlier if p['used_draws']>=boundary+full['minimum']]
        if len(eligible)<2:continue
        initial=(full['boundary_gains'][j] if kind=='detected' else full['proposal_gain'])/full['penalty']
        strengths=[initial];matches=0
        for past in eligible:
            boundaries=_boundaries(past,kind)
            if not boundaries:continue
            nearest=int(np.argmin(abs(np.asarray(boundaries)-boundary)))
            if abs(boundaries[nearest]-boundary)<=tolerance:
                matches+=1;gain=past['boundary_gains'][nearest] if kind=='detected' else past['proposal_gain']
                strengths.append(gain/past['penalty'])
        score=float(matches/len(eligible)*np.median(strengths)) if matches>=2 else 0.
        if score>best['score']:best=dict(score=score,boundary=int(boundary),matches=matches,eligible_prefixes=len(eligible))
    return best


def _concentration(fits,kind,n,tolerance):
    arrays=[np.asarray(_boundaries(fits[f'number{k:02d}'],kind),dtype=int) for k in range(1,46)]
    anchors=np.arange(13,n,13);counts=np.zeros(len(anchors),dtype=int)
    for values in arrays:
        if len(values):counts+=(abs(anchors[:,None]-values[None,:])<=tolerance).any(axis=1)
    i=int(np.argmax(counts));return float(counts[i]),int(anchors[i]) if counts[i]>0 else None


def _adjacent(x,fit,unit):
    best=0.;observed=dict(boundary=None)
    for i,boundary in enumerate(fit['boundaries']):
        start,end=fit['segments'][i][0],fit['segments'][i+1][1]
        before=x[start:boundary].mean(0);after=x[boundary:end].mean(0)
        if unit.startswith('number'):
            number=int(unit[6:])-1;value=float(abs(after[number]-before[number]))
            detail=dict(before_rate=float(before[number]),after_rate=float(after[number]))
        else:
            distance=distribution_distance(before,after);value=float(distance['l1']);detail=distance
        if value>best:
            best=value;observed=dict(boundary=int(boundary),before_start=int(start+1),after_end=int(end),
                before_support=int(boundary-start),after_support=int(end-boundary),**detail)
    return best,observed


def metric_vector(x,*,details=True):
    x=research_matrix(x);prefixes=prefix_sizes(len(x));prefix_fits={n:fit_prefix(x[:n]) for n in prefixes}
    full=prefix_fits[len(x)]['fits'];keys=[];values=[];families=[];metadata=[];observed=[];rows=[]
    def add(family,kind,value,observation=None,**parameters):
        key=kind+'/'+','.join(f'{k}={v}' for k,v in sorted(parameters.items()))
        meta=dict(family=family,kind=kind,**parameters);observation={} if observation is None else observation
        keys.append(key);values.append(float(value));families.append(family);metadata.append(meta);observed.append(observation)
        if details:rows.append(dict(key=key,**meta,oriented_value=float(value),**observation))
    for key,minimum,multiplier in configurations():
        fits=full[key]
        for unit in UNITS:
            fit=fits[unit];family='single_number' if unit.startswith('number') else 'global_shift'
            effect,obs=_adjacent(x,fit,unit)
            params=dict(unit=unit,minimum=minimum,multiplier=multiplier)
            add(family,'detected_effect' if family=='single_number' else 'detected_l1',effect,obs,**params)
            add(family,'proposal_gain',fit['proposal_gain'],dict(boundary=fit['proposal_boundary'],penalty=fit['penalty']),**params)
            earlier=[prefix_fits[n]['fits'][key][unit] for n in prefixes[:-1]]
            for kind in ('detected','proposal'):
                for tolerance in TOLERANCES:
                    s=stable_boundary(fit,earlier,tolerance=tolerance,kind=kind)
                    add('stability',kind+'_stability',s['score'],{k:v for k,v in s.items() if k!='score'},tolerance=tolerance,**params)
        for kind in ('detected','proposal'):
            groups={'number_union':sorted({b for unit in UNITS[:45] for b in _boundaries(fits[unit],kind)})}
            groups.update({unit:_boundaries(fits[unit],kind) for unit in GLOBAL_UNITS})
            for tolerance in TOLERANCES:
                count,boundary=_concentration(fits,kind,len(x),tolerance)
                add('concentration',kind+'_number_concentration',count,dict(boundary=boundary),minimum=minimum,multiplier=multiplier,tolerance=tolerance)
                for left,right in combinations(groups,2):
                    c=boundary_concordance(groups[left],groups[right],tolerance=tolerance)
                    add('concordance',kind+'_concordance',c['f1'],dict(matches=c['matches'],count_a=c['count_a'],count_b=c['count_b']),
                        minimum=minimum,multiplier=multiplier,tolerance=tolerance,left=left,right=right)
    number_cusum=cusum(x.astype(float),minimum=26)
    for j in range(45):
        add('single_number','number_cusum',number_cusum['score'][j],dict(boundary=int(number_cusum['location'][j]) if number_cusum['location'][j]>=0 else None),unit=f'number{j+1:02d}')
    shape_cusum=cusum(shape_vector(x),minimum=26)
    for j in range(7):add('global_shift','shape_cusum',shape_cusum['score'][j],dict(boundary=int(shape_cusum['location'][j]) if shape_cusum['location'][j]>=0 else None),feature=j)
    positions=np.arange(26,len(x)-26+1);scores=np.linalg.norm(number_cusum['curve'][positions],axis=1)/np.sqrt(45)
    selected=int(np.argmax(scores));add('global_shift','number_vector_cusum',scores[selected],dict(boundary=int(positions[selected]) if scores[selected]>1e-12 else None))
    return dict(draws=len(x),keys=keys,values=np.array(values),families=families,metadata=metadata,observed=observed,rows=rows,
        representation_hash=sha256(x.tobytes()).hexdigest(),space=dict(cells=len(keys),family_cells={f:families.count(f) for f in FAMILIES},
        units_per_prefix=50,configurations_per_prefix=300,prefixes=prefixes,penalty_multipliers=list(MULTIPLIERS),minimum_draws=list(MINIMUMS),
        prefix_inventory={str(n):dict(configurations=prefix_fits[n]['inventory'],contexts=prefix_fits[n]['context_sizes']) for n in prefixes}))


def fit_calibration(n,*,replicates=32,seed=191001,progress=None):
    prefix_sizes(n)
    if type(replicates) is not int or replicates<4:raise ValueError('At least4 independent pilots required')
    vectors=[];raw=None
    for i in range(replicates):
        child=int(np.random.SeedSequence([seed,n,i]).generate_state(1)[0]);raw=metric_vector(iid_surrogate(n,seed=child),details=False)
        vectors.append(raw['values'])
        if progress:progress(f'Calibration {n}: {i+1}/{replicates}')
    matrix=np.array(vectors);finite=np.isfinite(matrix).sum(0);mean=np.nanmean(matrix,axis=0);std=np.nanstd(matrix,axis=0,ddof=1)
    return dict(draws=n,replicates=replicates,seed=seed,keys=raw['keys'],families=raw['families'],metadata=raw['metadata'],space=raw['space'],
        mean=mean,std=std,finite_count=finite,eligible=(finite>=max(4,int(np.ceil(.75*replicates))))&(std>1e-12),pilot_values=matrix)


def standardize(raw,c):
    if raw['draws']!=c['draws'] or raw['keys']!=c['keys']:raise ValueError('Calibration cutoff/search identity mismatch')
    z=np.full(len(raw['keys']),np.nan);active=np.asarray(c['eligible'],dtype=bool)&np.isfinite(raw['values'])
    z[active]=(raw['values'][active]-np.asarray(c['mean'])[active])/np.asarray(c['std'])[active];return z


def complete_search(raw,c):
    z=standardize(raw,c);maxima={};leaders={}
    for family in FAMILIES:
        indices=np.flatnonzero((np.array(raw['families'])==family)&np.isfinite(z))
        if not len(indices):raise ValueError(f'No eligible {family} search cells')
        selected=int(indices[np.argmax(z[indices])]);maxima[family]=float(z[selected])
        leaders[family]=dict(key=raw['keys'][selected],z=float(z[selected]),oriented_value=float(raw['values'][selected]),
            **raw['metadata'][selected],**raw['observed'][selected])
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],eligible_cells=int(np.isfinite(z).sum()),representation_hash=raw['representation_hash'])


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


def null_search(x,calibrations,*,replicates=199,seed=190042,workers=1,include_development=True,progress=None):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
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
        with ProcessPoolExecutor(max_workers=workers,initializer=_initialize_worker,initargs=(x,c,include_development)) as pool:consume(pool.map(_worker_job,jobs))
    return rows


def compare_maxima(real,rows,*,scope):
    result=[]
    for kind in ('iid','fixed_margins'):
        group=[r[scope] for r in rows if r['null_model']==kind]
        if not group:raise ValueError('Both null families required')
        for family in FAMILIES:
            null=np.array([r['maxima'][family] for r in group]);observed=real['maxima'][family]
            exceed=int((null>=observed).sum());p=(1+exceed)/(len(null)+1)
            result.append(dict(scope=scope,cutoff=real['draws'],null_model=kind,family=family,real_max=observed,
                null_mean=float(null.mean()),null_q95=float(np.quantile(null,.95)),exceedances=exceed,
                replicates=len(null),global_p=p,adjusted_p=min(1,5*p)))
    return result
