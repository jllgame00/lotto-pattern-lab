"""H10: bounded representations and identical, global-maximum surrogate searches."""
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.analysis.wavelet import PERIODS,morlet_transform,localized_regions
from src.analysis.ssa import WINDOWS,decompose,candidate_pairs

FAMILIES=('wavelet_peak','wavelet_region','wavelet_concentration',
          'ssa_leading','ssa_pair','ssa_stability')
ENDPOINTS=(416,624,832,1040,1245)
SHAPES=('sum','mean','range','std','spacing_mean','spacing_std','consecutive_pairs','odd_count')


def representations(x,*,cutoff):
    x=research_matrix(x)
    if type(cutoff) is not int or cutoff!=len(x):raise ValueError('Exact causal prefix required')
    numbers=(np.nonzero(x)[1]+1).reshape(-1,6);spacing=np.diff(numbers,axis=1)
    shape=np.column_stack((numbers.sum(1),numbers.mean(1),np.ptp(numbers,axis=1),
        numbers.std(1),spacing.mean(1),spacing.std(1),(spacing==1).sum(1),(numbers%2==1).sum(1)))
    return [f'number_{n}' for n in range(1,46)]+list(SHAPES),np.column_stack((x,shape)).astype(float)


def complete_search(x,*,periods=PERIODS,lengths=WINDOWS,endpoints=ENDPOINTS,window=416):
    """No real-selected locations are inputs: every history chooses its own maxima."""
    names,y=representations(x,cutoff=len(x))
    if not endpoints or any(type(e) is not int or not window<=e<=len(x) for e in endpoints):
        raise ValueError('Fixed historical SSA windows must be available')
    if sorted(set(endpoints))!=list(endpoints):raise ValueError('Ordered unique window endpoints required')
    transform=morlet_transform(y,periods=periods)
    power=transform['power'];valid=transform['valid'];periods=np.asarray(transform['periods'])
    regions=localized_regions(transform,names=names,min_cycles=2,threshold=4.)
    maxima=dict.fromkeys(FAMILIES,0.);leaders={};wrows=[];srows=[]
    for i,name in enumerate(names):
        masked=np.where(valid,power[i],-np.inf)
        scale,time=np.unravel_index(np.argmax(masked),masked.shape)
        gp=np.array([power[i,j,valid[j]].mean() for j in range(len(periods))])
        concentration=float(gp.max()/gp.sum()) if gp.sum()>0 else 0.
        own=[r for r in regions if r['series']==i]
        strongest=max(own,key=lambda r:r['score']) if own else None
        row=dict(series=name,wavelet_peak=float(masked[scale,time]),peak_draw=int(time+1),
            peak_period=float(periods[scale]),wavelet_concentration=concentration,
            wavelet_region=float(strongest['score']) if strongest else 0.,
            region_count=len(own),global_power=gp.tolist())
        wrows.append(row)
        for family in FAMILIES[:3]:
            if family not in leaders or row[family]>maxima[family]:
                maxima[family]=row[family];leaders[family]=dict(row,region=strongest)
    previous={}
    for end in endpoints:
        current={}
        for i,name in enumerate(names):
            for length in lengths:
                result=decompose(y[end-window:end,i],length,components=8)
                pairs=candidate_pairs(result,min_period=8,max_period=104)
                leading=float(result['energy_ratios'][0])
                pair=max(pairs,key=lambda p:p['score']) if pairs else None
                stable=0.;match=None
                for p in pairs:
                    for q in previous.get((i,length),[]):
                        period_ratio=min(p['period'],q['period'])/max(p['period'],q['period'])
                        amplitude_ratio=min(p['amplitude'],q['amplitude'])/max(p['amplitude'],q['amplitude'],1e-12)
                        if period_ratio>=1/1.2 and amplitude_ratio>=.5:
                            score=min(p['score'],q['score'])*period_ratio*amplitude_ratio
                            if score>stable:stable=float(score);match=dict(current=p,previous=q)
                row=dict(series=name,start=end-window+1,end=end,L=length,ssa_leading=leading,
                    ssa_pair=float(pair['score']) if pair else 0.,ssa_stability=stable,
                    singular_values=result['singular_values'].tolist(),
                    energy_ratios=result['energy_ratios'].tolist(),residual_variance=float(result['residual_variance']),
                    pairs=pairs,stability_match=match)
                srows.append(row);current[(i,length)]=pairs
                for family in FAMILIES[3:]:
                    if family not in leaders or row[family]>maxima[family]:maxima[family]=row[family];leaders[family]=row
        previous=current
    space=dict(series=53,numbers=45,shapes=8,periods=list(map(float,periods)),
        wavelet_coefficients=int(valid.sum()*53),wavelet_global_cells=53*len(periods),
        wavelet_region_grid_cells=int(valid.sum()*53),ssa_windows=list(endpoints),window_length=window,
        ssa_L=list(lengths),ssa_decompositions=53*len(endpoints)*len(lengths),
        ssa_pair_candidates=53*len(endpoints)*len(lengths)*7,
        ssa_stability_pair_comparisons=53*(len(endpoints)-1)*len(lengths)*49,families=6)
    return dict(maxima=maxima,leaders=leaders,wavelet_rows=wrows,ssa_rows=srows,regions=regions,
        space=space,representation_hash=sha256(y.tobytes()).hexdigest())


def _null_job(job):
    x,kind,code,i,seed,args=job
    child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
    null=iid_surrogate(len(x),seed=child) if code==0 else constrained_surrogate(x,seed=child)
    result=complete_search(null,**args)
    return dict(null_model=kind,replicate=i,seed=child,rebuilt=True,space=result['space'],
        representation_hash=result['representation_hash'],changed_fraction=float((x!=null).mean()),**result['maxima'])


def null_search(x,*,replicates=199,seed=120042,search_args=None,progress=None,workers=1):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:
        raise ValueError('Positive replicate and worker counts required')
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
    result=[]
    for kind in ('iid','fixed_margins'):
        group=[r for r in rows if r['null_model']==kind]
        if not group:raise ValueError('Both null families required')
        for family in FAMILIES:
            values=np.array([r[family] for r in group]);value=real['maxima'][family]
            exceed=int((values>=value).sum());p=(exceed+1)/(len(values)+1)
            result.append(dict(null_model=kind,family=family,real_max=value,null_mean=float(values.mean()),
                null_q95=float(np.quantile(values,.95)),exceedances=exceed,replicates=len(values),
                global_p=p,adjusted_p=min(1.,6*p)))
    return result
