"""H24 complete predeclared search; every null refits its initial200 boundaries."""
from hashlib import sha256
import json
import numpy as np
from .recurrence import research_matrix
from .spatiotemporal import iid_surrogate,constrained_surrogate
from .symbolic import (ALPHAS,LAGS,encode_all,support_audit,conditional_entropy,prequential_losses,
    transition_diagnostic,word_diagnostic,run_diagnostic,symbolic_lag,select_order)

FAMILIES=('entropy','heldout','transition','word','forbidden','run_lag')


def metric_vector(x,*,details=False):
    x=research_matrix(x);n=len(x)
    if n not in (900,1245):raise ValueError('H24 complete scope must be900 or1245 draws')
    encodings=encode_all(x);keys=[];families=[];metadata=[];values=[];inventory={}
    split=400 if n==900 else 700
    def add(family,encoding,name,value,**meta):
        keys.append(f'{family}|{encoding}|{name}');families.append(family);values.append(float(value))
        metadata.append(dict(family=family,encoding=encoding,statistic=name,**meta))
    for name,encoding in encodings.items():
        s=encoding['symbols'];A=encoding['alphabet'];H=[conditional_entropy(s,A,k) for k in range(4)]
        losses=prequential_losses(s,A);means=losses[split:].mean(0)
        for k in (1,2,3):
            add('entropy',name,f'order{k}',H[0]-H[k],order=k)
            for ai,alpha in enumerate(ALPHAS):
                add('heldout',name,f'order{k}_alpha{alpha}',means[0,ai]-means[k,ai],order=k,alpha=alpha)
        transition=transition_diagnostic(s,A)
        for tail in ('positive','negative'):
            leader=transition[tail];add('transition',name,tail,leader['value'],tail=tail,source=leader['source'],
                destination=leader['destination'],count=leader['count'],expected=leader['expected'])
        words={};longest_absent=0
        for L in (2,3,4):
            r=word_diagnostic(s,A,L);words[L]=r
            for tail in ('positive','negative'):
                leader=r[tail];add('word',name,f'L{L}_{tail}',leader['value'],length=L,tail=tail,
                    word=leader['word'],count=leader['count'],expected=leader['expected'],lift=leader['lift'],eligible_word_count=r['eligible'])
            for stat in ('missing_max_expected','missing_fraction','rare_max_expected'):
                add('forbidden',name,f'L{L}_{stat}',r[stat],length=L,eligible_word_count=r['eligible'],
                    missing_count=r['missing_count'],rare_count=r['rare_count'])
            if r['missing_count']:longest_absent=L
        add('forbidden',name,'longest_absent_length',longest_absent)
        run=run_diagnostic(s,A)
        for stat in ('longest','order0_surprise','order1_surprise','away_gap'):add('run_lag',name,stat,run[stat])
        for lag in LAGS:add('run_lag',name,f'lag{lag}',abs(symbolic_lag(s,A,lag)),lag=lag)
        if details:inventory[name]=dict(**encoding,support=support_audit(s,A),entropy=H,losses=means,
            loss_series=losses,split=split,transition=transition,words=words,runs=run,selection=select_order(s,A,split))
    encoding_hash=sha256(b''.join(v['symbols'].tobytes()+json.dumps(v['boundaries']).encode() for v in encodings.values())).hexdigest()
    alphabet={k:v['alphabet'] for k,v in encodings.items()}
    word_space={name:{str(L):A**L for L in (2,3,4)} for name,A in alphabet.items()}
    space=dict(cells=len(keys),family_cells={f:families.count(f) for f in FAMILIES},alphabets=alphabet,orders=[0,1,2,3],
        alphas=list(ALPHAS),word_lengths=[2,3,4],word_candidates=word_space,
        total_word_candidates=sum(sum(v.values()) for v in word_space.values()),
        transition_candidates=sum(A*A for A in alphabet.values()),symbol_lags=list(LAGS),fit_end=200,
        state_rare_below=5,transition_source_min=20,transition_destination_min=5,expected_min=5,
        word_prefix_min=10,context_min=20,bin_update='frozen after200',score='upper pilot z')
    out=dict(draws=n,keys=keys,families=families,metadata=metadata,values=np.array(values),space=space,
        representation_hash=sha256(x.tobytes()).hexdigest(),encoding_hash=encoding_hash,analysis_start=201,
        validation_start=601 if n==900 else 901)
    if details:out['inventory']=inventory
    return out


def fit_calibration(n,*,replicates=32,seed=251001,progress=None):
    if n not in (900,1245) or type(replicates) is not int or replicates<4:raise ValueError('900/1245 and at least4 pilots required')
    values=[]
    for i in range(replicates):
        child=int(np.random.SeedSequence([seed,n,i]).generate_state(1)[0])
        raw=metric_vector(iid_surrogate(n,seed=child));values.append(raw['values'])
        if progress:progress(f'Pilot {n}: {i+1}/{replicates}')
    a=np.array(values);mean=a.mean(0);raw_std=a.std(0,ddof=1)
    std=np.where(raw_std>1e-12,raw_std,1.)
    return dict(draws=n,replicates=replicates,seed=seed,keys=raw['keys'],families=raw['families'],space=raw['space'],
        mean=mean,std=std,raw_std=raw_std,eligible=np.isfinite(std),pilot_values=a,
        constant_scale_rule='Pilot std<=1e-12 uses fixed unit scale; no cell is dropped')


def standardize(raw,c):
    if raw['draws']!=c['draws'] or raw['keys']!=c['keys']:raise ValueError('Calibration scope/search mismatch')
    z=np.full(len(raw['keys']),np.nan);active=np.asarray(c['eligible'])&np.isfinite(raw['values'])
    z[active]=(raw['values'][active]-np.asarray(c['mean'])[active])/np.asarray(c['std'])[active]
    return z


def complete_search(raw,c):
    z=standardize(raw,c);families=np.array(raw['families']);maxima={};leaders={}
    for family in FAMILIES:
        indices=np.flatnonzero((families==family)&np.isfinite(z))
        if not len(indices):raise ValueError(f'No eligible cells for {family}')
        i=int(indices[np.argmax(z[indices])]);maxima[family]=float(z[i])
        leaders[family]=dict(index=i,key=raw['keys'][i],value=float(raw['values'][i]),z=float(z[i]),**raw['metadata'][i])
    return dict(draws=raw['draws'],maxima=maxima,leaders=leaders,space=raw['space'],eligible_cells=int(np.isfinite(z).sum()),
        representation_hash=raw['representation_hash'],encoding_hash=raw['encoding_hash'])


def null_search(x,calibrations,*,replicates=199,seed=250042,include_development=True,progress=None):
    x=research_matrix(x)
    if include_development and len(x)!=1245:raise ValueError('Full+development requires exact1..1245')
    if type(replicates) is not int or replicates<1:raise ValueError('Positive replicate count required')
    rows=[]
    for kind,code in [('iid',0),('fixed_margins',1)]:
        for i in range(replicates):
            row=dict(null_model=kind,replicate=i)
            for scope,actual in [('full',x)]+([('development',x[:900])] if include_development else []):
                n=len(actual);child=int(np.random.SeedSequence([seed,code,i,n]).generate_state(1)[0])
                null=iid_surrogate(n,seed=child) if kind=='iid' else constrained_surrogate(actual,seed=child)
                raw=metric_vector(null)
                row[scope]=dict(complete_search(raw,calibrations[n]),seed=child,rebuilt=True,raw_values=raw['values'],
                    row_six=bool((null.sum(1)==6).all()),changed_fraction=float((null!=actual).mean()),
                    fixed_margins_preserved=bool(np.array_equal(null.sum(0),actual.sum(0))) if kind!='iid' else None)
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
            p=(1+int((a>=obs).sum()))/(len(a)+1)
            out.append(dict(scope=scope,null_model=kind,family=family,real_max=obs,null_median=float(np.median(a)),
                global_p=p,adjusted_p=min(1.,6*p),replicates=len(a)))
    return out


def development_selection(x,c,rows):
    x=research_matrix(x)
    if len(x)!=900 or c.get('draws')!=900:raise ValueError('Development requires exact1..900')
    raw=metric_vector(x,details=True);found=complete_search(raw,c);comparison=compare_maxima(found,rows,scope='development')
    passing=[f for f in FAMILIES if all(r['adjusted_p']<=.05 for r in comparison if r['family']==f)]
    choices={};qualified=[]
    for name,r in raw['inventory'].items():
        choice=r['selection'];order=choice['order'];alpha=choice['alpha'];ai=ALPHAS.index(alpha)
        era_gains=[float((r['loss_series'][part,0,ai]-r['loss_series'][part,order,ai]).mean())
            for part in np.array_split(np.arange(r['split'],len(r['symbols'])),3)]
        evidence=[]
        for family,key in [('heldout',f'order{order}_alpha{alpha}'),('entropy',f'order{order}')]:
            index=raw['keys'].index(f'{family}|{name}|{key}') if order else None
            z=float((raw['values'][index]-c['mean'][index])/c['std'][index]) if index is not None and c['eligible'][index] else 0.
            for kind in ('iid','fixed_margins'):
                maxima=np.array([row['development']['maxima'][family] for row in rows if row['null_model']==kind])
                p=(1+int((maxima>=z).sum()))/(len(maxima)+1) if z>0 else 1.
                evidence.append(dict(family=family,null_model=kind,signed_z=z,global_p=p,adjusted_p=min(1.,6*p)))
        supported=order>0 and choice['gain_lower']>.01 and all(v>0 for v in era_gains) and all(e['adjusted_p']<=.05 for e in evidence)
        choices[name]=dict(choice,validation_era_gains=era_gains,evidence=evidence,supported=supported,
            boundaries=r['boundaries'],alphabet=r['alphabet'])
        if supported and 'entropy' in passing and 'heldout' in passing:qualified.append(name)
    selected=max(qualified,key=lambda name:choices[name]['gain_order0']) if qualified else None
    descriptive=min(choices,key=lambda name:(-choices[name]['gain_order0'],choices[name]['order'],name))
    return dict(training_cutoff=900,training_hash=sha256(x.tobytes()).hexdigest(),later_start=901,
        fit_end=200,selection_validation=[601,900],passing_families=passing,choices=choices,
        selected_encoding=selected,descriptive_best=descriptive,predictive_model_justified=bool(selected),
        decision='SYMBOLIC_MODEL_IMPLEMENTATION_REQUIRED' if selected else 'PREDICTIVE_MODEL_NOT_JUSTIFIED',
        ensemble_decision='PENDING_LATER_EVALUATION' if selected else 'NOT CURRENTLY JUSTIFIED',comparison=comparison)
