"""Complete bounded gap-conditioned searches; all inference uses surrogate maxima."""
from dataclasses import dataclass,asdict
import numpy as np
import pandas as pd
from scipy.signal import fftconvolve
from src.analysis.gap3d import causal_states,GapEncoder
from src.analysis.spatiotemporal import binary_matrix,aligned,iid_surrogate,constrained_surrogate,P


@dataclass(frozen=True)
class Search3DConfig:
    max_dt:int=52
    max_dn:int=15
    trajectory_dt:int=13
    trajectory_dn:int=6
    delta_gap:int=3
    min_support:int=100
    chain_support:int=20

    def __post_init__(self):
        if any(type(v) is not int or v<1 for v in asdict(self).values()) or max(self.max_dn,self.trajectory_dn)>44:
            raise ValueError('Positive bounded integer search parameters required')


def _grid(max_dt,max_dn):
    return np.repeat(np.arange(1,max_dt+1),2*max_dn),np.tile(np.r_[np.arange(-max_dn,0),np.arange(1,max_dn+1)],max_dt)


def _cross(a,b,dt,dn):
    values=np.rint(fftconvolve(a[::-1,::-1].astype(float),b.astype(float))).astype(int)
    return values[len(a)-1+dt,44+dn]


def _opportunities(mask,dt,dn):
    prefix=np.pad(np.cumsum(np.cumsum(mask,axis=0),axis=1),((1,0),(1,0)))
    return prefix[len(mask)-dt,np.minimum(45,45-dn)]-prefix[len(mask)-dt,np.maximum(0,-dn)]


def statistics(table,min_support):
    table=table.copy(); n=table.valid_opportunities.to_numpy(dtype=float); k=table.matches.to_numpy(dtype=float)
    rate=np.divide(k,n,out=np.full(len(n),np.nan),where=n>0)
    root=np.sqrt(n*P*(1-P))
    table['match_rate']=rate; table['expected_rate']=P; table['lift']=rate/P
    table['raw_z']=np.divide(k-n*P,root,out=np.zeros(len(n)),where=n>0)
    table['search_eligible']=n>=min_support
    safe=np.maximum(n,1); z=1.959963984540054; center=(np.nan_to_num(rate)+z*z/(2*safe))/(1+z*z/safe)
    half=z*np.sqrt(np.nan_to_num(rate)*(1-np.nan_to_num(rate))/safe+z*z/(4*safe**2))/(1+z*z/safe)
    table['wilson_low']=np.where(n>0,np.maximum(0,center-half),np.nan)
    table['wilson_high']=np.where(n>0,np.minimum(1,center+half),np.nan)
    table['interval_scope']='marginal Wilson; not search-adjusted; dependence ignored'
    return table


def conditional_scores(x,states,*,state_count,max_dt=52,max_dn=15,min_support=100):
    x=binary_matrix(x); states=np.asarray(states)
    if states.shape!=x.shape or not 1<=max_dt<len(x): raise ValueError('Invalid state shape or shift range')
    dt,dn=_grid(max_dt,max_dn); frames=[]
    for state in range(state_count):
        source=x&(states==state)
        frames.append(pd.DataFrame(dict(delta_draw=dt,delta_number=dn,gap_state=state,
            source_observations=int(source.sum()),valid_opportunities=_opportunities(source,dt,dn),
            matches=_cross(source,x,dt,dn))))
    return statistics(pd.concat(frames,ignore_index=True),min_support)


def destination_scores(x,states,config):
    dt,dn=_grid(config.max_dt,config.max_dn); frames=[]
    for a in range(3):
        source=x&(states==a)
        for b in range(3):
            destination=states==b
            frames.append(pd.DataFrame(dict(delta_draw=dt,delta_number=dn,source_state=a,destination_state=b,
                valid_opportunities=_cross(source,destination,dt,dn),matches=_cross(source,destination&x,dt,dn),
                usage='DESCRIPTIVE_ONLY')))
    return statistics(pd.concat(frames,ignore_index=True),config.min_support)


def displacement_scores(x,gap,config):
    rows=[]
    for dt in range(1,config.trajectory_dt+1):
        for dn in range(-config.trajectory_dn,config.trajectory_dn+1):
            if dn==0: continue
            a,b=aligned(x,dt,dn); ga,gb=aligned(gap,dt,dn)
            for dg in range(-config.delta_gap,config.delta_gap+1):
                opportunities=a&(ga>=0)&(gb>=0)&(gb-ga==dg)
                rows.append(dict(delta_draw=dt,delta_number=dn,delta_gap=dg,
                    valid_opportunities=int(opportunities.sum()),matches=int((opportunities&b).sum()),usage='DESCRIPTIVE_ONLY'))
    return statistics(pd.DataFrame(rows),config.min_support)


def trajectory_search(x,gap,states,*,cap,max_dt=13,max_dn=6,delta_gap=3,min_support=20,details=True):
    """Maximal paths only; all intermediate pre-states must obey the rule.

    The continuation denominator requires L-1 observed predecessors and the
    final pre-draw state condition, never the final outcome. Descriptive only.
    """
    rows=[]; paths=[]; longest=0; geometric_configurations=0
    for dt in range(1,max_dt+1):
        for dn in range(-max_dn,max_dn+1):
            if dn==0: continue
            for kind,rules in [('same_bin',range(3)),('delta_gap',range(-delta_gap,delta_gap+1))]:
                for rule in rules:
                    maximum=min((len(x)-1)//dt,44//abs(dn))+1
                    if kind=='delta_gap' and rule: maximum=min(maximum,cap//abs(rule)+1)
                    geometric_configurations+=max(0,maximum-2)
                    allowed=(states==rule) if kind=='same_bin' else (gap>=0)
                    active=x&allowed; lengths=active.astype(np.int16) if details else None
                    for length in range(2,maximum+1):
                        step=length-1; a,b=aligned(x,dt,dn,step)
                        ga,gb=aligned(gap,dt,dn,step)
                        tlen,nlen=a.shape; offset=0 if dn>0 else -step*dn
                        state_condition=aligned(states,dt,dn,step)[1]==rule if kind=='same_bin' else (gb>=0)&(ga>=0)&(gb-ga==step*rule)
                        eligible=active[:tlen,offset:offset+nlen]&state_condition
                        continued=eligible&b; count=int(continued.sum())
                        if length in (3,4,5): rows.append(dict(kind=kind,rule=rule,delta_draw=dt,delta_number=dn,
                            chain_length=length,valid_opportunities=int(eligible.sum()),matches=count,
                            geometric_starts=(len(x)-step*dt)*(45-step*abs(dn))))
                        following=np.zeros_like(x); following[:tlen,offset:offset+nlen]=continued; active=following
                        if count:
                            if length>=3: longest=max(longest,length)
                            if details: lengths[active]=length
                        elif length>=5: break
                    if not details: continue
                    predecessor=np.zeros_like(x); a,b=aligned(x,dt,dn); ga,gb=aligned(gap,dt,dn)
                    previous=(a&aligned(allowed,dt,dn)[0])
                    if kind=='delta_gap': previous &= (ga>=0)&(gb>=0)&(gb-ga==rule)
                    if dn>0: predecessor[dt:,dn:]=previous
                    else: predecessor[dt:,:45+dn]=previous
                    ts,ns=np.where((lengths>=3)&~predecessor)
                    for t,n in zip(ts,ns):
                        length=int(lengths[t,n]); geom=min((len(x)-1-t)//dt,(44-n)//dn if dn>0 else n//(-dn))+1
                        if kind=='delta_gap' and rule:
                            geom=min(geom,(cap-int(gap[t,n]))//rule+1 if rule>0 else int(gap[t,n])//(-rule)+1)
                        paths.append(dict(kind=kind,rule=rule,start_draw=int(t+1),start_number=int(n+1),start_gap=int(gap[t,n]),
                            delta_draw=dt,delta_number=dn,delta_gap=rule if kind=='delta_gap' else np.nan,
                            chain_length=length,support=length,geometric_maximum=geom,
                            end_draw=int(t+1+(length-1)*dt),end_number=int(n+1+(length-1)*dn),
                            overlaps_longer=False,nested_fragments_suppressed=(length-1)*(length-2)//2-1))
    frame=pd.DataFrame(rows)
    if len(frame): frame=statistics(frame,min_support)
    return frame,pd.DataFrame(paths),longest,geometric_configurations


def _maximum(frame):
    if frame.empty: return 0.
    values=frame.loc[frame.search_eligible,'raw_z']
    return max(0.,float(values.max())) if len(values) else 0.


def trajectory_position_count(length,cap,config):
    """All geometrically possible (rule,length,start cell) tests, including zeros.

    Counts positional searches explicitly; data-driven pruning changes runtime,
    not the effective exhaustive search or this geometric count.
    """
    total=0
    for dt in range(1,config.trajectory_dt+1):
        for dn in range(-config.trajectory_dn,config.trajectory_dn+1):
            if not dn: continue
            maximum=min((length-1)//dt,44//abs(dn))+1
            maxima=[maximum]*3+[min(maximum,cap//abs(dg)+1) if dg else maximum for dg in range(-config.delta_gap,config.delta_gap+1)]
            for maximum in maxima:
                total+=sum((length-step*dt)*(45-step*abs(dn)) for step in range(2,maximum))
    return int(total)


def search3d(x,config=Search3DConfig(),*,details=True):
    x=binary_matrix(x)
    if max(config.max_dt,config.trajectory_dt)>=len(x): raise ValueError('Search exceeds history')
    g,m,r=causal_states(x); g,r=g[:-1],r[:-1]
    encoder=GapEncoder().fit(g,r,cutoff=len(x))
    conditional=[]
    for representation in ('quantile','clipped','relative'):
        encoded=encoder.transform(g,r,representation)
        table=conditional_scores(x,encoded,state_count=encoder.count(representation),max_dt=config.max_dt,
            max_dn=config.max_dn,min_support=config.min_support)
        table['representation']=representation; conditional.append(table)
    conditional=pd.concat(conditional,ignore_index=True)
    states=encoder.transform(g,r); clipped=encoder.transform(g,r,'clipped')
    destination=destination_scores(x,states,config); displacement=displacement_scores(x,clipped,config)
    counts,paths,longest,geometry=trajectory_search(x,clipped,states,cap=encoder.cap,
        max_dt=config.trajectory_dt,max_dn=config.trajectory_dn,delta_gap=config.delta_gap,
        min_support=config.chain_support,details=details)
    if len(paths):
        paths['start_gap_clipped']=paths.start_gap
        paths['start_gap']=g[paths.start_draw.to_numpy()-1,paths.start_number.to_numpy()-1].astype(int)
    maxima=dict(conditional=_maximum(conditional),destination=_maximum(destination),displacement=_maximum(displacement),
        trajectory=_maximum(counts),longest_trajectory=int(longest))
    space=dict(conditional=len(conditional),destination=len(destination),displacement=len(displacement),
        trajectory_length_3_4_5=len(counts),trajectory_all_geometric_lengths=geometry,
        total_unique_configurations=len(conditional)+len(destination)+len(displacement)+geometry,
        trajectory_rule_length_start_positions=trajectory_position_count(len(x),encoder.cap,config),
        eligible_conditional=int(conditional.search_eligible.sum()),eligible_destination=int(destination.search_eligible.sum()),
        eligible_displacement=int(displacement.search_eligible.sum()),eligible_trajectory=int(counts.search_eligible.sum()) if len(counts) else 0)
    return dict(conditional=conditional,destination=destination,displacement=displacement,
        trajectories=counts,maximal_trajectories=paths,maxima=maxima,search_space=space,encoder=encoder.configuration())


def compare_nulls3d(x,config=Search3DConfig(),*,replicates=199,seed=70042,progress=None):
    x=binary_matrix(x)
    if not np.all(x.sum(axis=1)==6) or type(replicates) is not int or replicates<1: raise ValueError('Valid Lotto rows and positive replicates required')
    observed=search3d(x,config,details=False); rows=[]; follow=[]
    for kind,code in [('iid',0),('fixed_margins',1)]:
        for i in range(replicates):
            child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
            surrogate=iid_surrogate(len(x),seed=child) if kind=='iid' else constrained_surrogate(x,seed=child)
            result=search3d(surrogate,config,details=False)
            rows.append(dict(null_model=kind,replicate=i,seed=child,gap_recomputed=True,encoder_refitted=True,
                cap=result['encoder']['clip_cap'],**result['maxima'],**{'space_'+k:v for k,v in result['search_space'].items()}))
            f=result['conditional'].query('delta_draw==42 and delta_number==-5 and representation=="quantile"').copy()
            f['null_model']=kind; f['replicate']=i; follow.append(f)
            if progress and (i+1)%10==0: progress(f'{kind}: complete conditional/3D searches{i+1}/{replicates}')
    null=pd.DataFrame(rows); comparisons=[]
    for kind,group in null.groupby('null_model'):
        for statistic,value in observed['maxima'].items():
            exceeds=int((group[statistic]>=value).sum()); p=(1+exceeds)/(replicates+1)
            comparisons.append(dict(null_model=kind,statistic=statistic,real_max=value,null_mean=float(group[statistic].mean()),
                null_q95=float(group[statistic].quantile(.95)),exceedances=exceeds,replicates=replicates,global_p=p,adjusted_p=min(1,p*5)))
    return pd.DataFrame(comparisons),null,pd.concat(follow,ignore_index=True)
