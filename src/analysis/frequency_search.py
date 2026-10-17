"""Complete frequency-conditioned searches, pooled across all declared windows."""
from dataclasses import dataclass,asdict
from types import SimpleNamespace
import numpy as np
import pandas as pd
from src.analysis.frequency3d import WINDOWS,frequency_states,FrequencyEncoder
from src.analysis.spatiotemporal import binary_matrix,iid_surrogate,constrained_surrogate,P
from src.analysis.gap3d_search import (_cross,_opportunities,statistics,displacement_scores,
    trajectory_search,trajectory_position_count,_maximum)
# Reuse tested geometric arithmetic only. No gap histories/features are constructed.

@dataclass(frozen=True)
class FrequencySearchConfig:
    max_dt:int=52
    max_dn:int=15
    trajectory_dt:int=13
    trajectory_dn:int=6
    delta_count:int=1
    min_support:int=100
    chain_support:int=20
    def __post_init__(self):
        if any(type(v) is not int or v<1 for v in asdict(self).values()) or max(self.max_dn,self.trajectory_dn)>44:
            raise ValueError('Positive bounded integer configuration required')

def conditional_frequency(x,states,*,state_count,max_dt=52,max_dn=15,min_support=100):
    x=binary_matrix(x); states=np.asarray(states)
    if states.shape!=x.shape or not 1<=max_dt<len(x) or not 1<=max_dn<=44: raise ValueError('Invalid search geometry')
    dt=np.repeat(np.arange(1,max_dt+1),2*max_dn+1);dn=np.tile(np.arange(-max_dn,max_dn+1),max_dt)
    frames=[]
    for state in range(state_count):
        source=x&(states==state)
        matches=_cross(source,x,dt,dn) if source.any() else np.zeros(len(dt),int)
        frames.append(pd.DataFrame(dict(delta_draw=dt,delta_number=dn,state=state,
            source_observations=int(source.sum()),valid_opportunities=_opportunities(source,dt,dn),matches=matches)))
    return statistics(pd.concat(frames,ignore_index=True),min_support)

def directional_scores(conditional,min_support):
    keys=['window','representation','state','delta_draw','delta_number']
    pos=conditional[conditional.delta_number>0].copy();neg=conditional[conditional.delta_number<0].copy()
    neg['delta_number']=-neg.delta_number
    merged=pos.merge(neg,on=keys,suffixes=('_positive','_negative'))
    n1,n2=merged.valid_opportunities_positive.to_numpy(),merged.valid_opportunities_negative.to_numpy()
    variance=P*(1-P)*(np.divide(1.,n1,out=np.full(len(n1),np.inf),where=n1>0)+np.divide(1.,n2,out=np.full(len(n2),np.inf),where=n2>0))
    merged['direction_difference']=merged.match_rate_positive-merged.match_rate_negative
    merged['variance_reference']=variance
    merged['raw_z']=merged.direction_difference/np.sqrt(variance)
    merged['search_eligible']=(n1>=min_support)&(n2>=min_support)
    merged['kind']='positive_minus_negative'
    hot=merged[(merged.representation=='quantile')&(merged.state==2)]
    cold=merged[(merged.representation=='quantile')&(merged.state==0)]
    joined=hot.merge(cold,on=['window','delta_draw','delta_number'],suffixes=('_hot','_cold'))
    interaction=joined[['window','delta_draw','delta_number']].copy()
    interaction['representation']='quantile';interaction['state']='HOT-COLD';interaction['kind']='hot_cold_direction_interaction'
    interaction['direction_difference']=joined.direction_difference_hot-joined.direction_difference_cold
    interaction['raw_z']=interaction.direction_difference/np.sqrt(joined.variance_reference_hot+joined.variance_reference_cold)
    interaction['search_eligible']=joined.search_eligible_hot&joined.search_eligible_cold
    result=pd.concat([merged,interaction],ignore_index=True)
    result['absolute_z']=result.raw_z.abs()
    result['interpretation']='dependent raw standardized contrast; inference requires complete surrogate maxima'
    return result

def search_frequency(x,config=FrequencySearchConfig(),*,details=True):
    x=binary_matrix(x)
    if len(x)<=max(52,config.max_dt,config.trajectory_dt): raise ValueError('Insufficient full-window history')
    tables={k:[] for k in ('conditional','displacement','trajectories','paths')};encoders={};geometric=0;positions=0;longest=0;window_max={}
    geometry=SimpleNamespace(**{**asdict(config),'delta_gap':config.delta_count})
    for window in WINDOWS:
        f={k:v[:-1] for k,v in frequency_states(x,window).items()}
        encoder=FrequencyEncoder(window).fit(f,cutoff=len(x));encoders[str(window)]=encoder.configuration()
        local=[]
        for representation in ('count','quantile','relative'):
            states=encoder.transform(f,representation)
            table=conditional_frequency(x,states,state_count=encoder.count(representation),max_dt=config.max_dt,
                max_dn=config.max_dn,min_support=config.min_support)
            table['window']=window;table['representation']=representation
            table['normalized_state_value']=table.state/window if representation=='count' else np.nan
            table['state_label']=table.state.astype(str) if representation=='count' else table.state.map({0:'COLD',1:'NEUTRAL',2:'HOT'})
            local.append(table)
        conditional=pd.concat(local,ignore_index=True);tables['conditional'].append(conditional)
        raw=encoder.transform(f,'count');coarse=encoder.transform(f)
        displacement=displacement_scores(x,raw,geometry).rename(columns={'delta_gap':'delta_count'});displacement['window']=window
        tables['displacement'].append(displacement)
        counts,paths,maximum,space=trajectory_search(x,raw,coarse,cap=window,max_dt=config.trajectory_dt,
            max_dn=config.trajectory_dn,delta_gap=config.delta_count,min_support=config.chain_support,details=details)
        counts=counts.replace({'kind':{'delta_gap':'delta_count'}});counts['window']=window
        if len(paths):
            paths=paths.rename(columns={'start_gap':'start_count','delta_gap':'delta_count'}).replace({'kind':{'delta_gap':'delta_count'}})
            paths['window']=window;paths['start_rate']=paths.start_count/window
        tables['trajectories'].append(counts);tables['paths'].append(paths)
        geometric+=space;positions+=trajectory_position_count(len(x),window,geometry);longest=max(longest,maximum)
        window_max[str(window)]=dict(conditional=_maximum(conditional),displacement=_maximum(displacement),trajectory=_maximum(counts),longest_trajectory=maximum)
    result={k:pd.concat(v,ignore_index=True) for k,v in tables.items()}
    directions=directional_scores(result['conditional'],config.min_support);result['directional']=directions
    def direction_max(table):
        values=table.loc[table.search_eligible,'absolute_z'];return max(0.,float(values.max())) if len(values) else 0.
    maxima=dict(conditional=_maximum(result['conditional']),directional=direction_max(directions),
        displacement=_maximum(result['displacement']),trajectory=_maximum(result['trajectories']),longest_trajectory=longest)
    for window in WINDOWS: window_max[str(window)]['directional']=direction_max(directions[directions.window==window])
    space=dict(conditional=len(result['conditional']),directional=len(directions),displacement=len(result['displacement']),
        trajectory_length_3_4_5=len(result['trajectories']),trajectory_all_geometric_lengths=geometric,
        trajectory_rule_length_start_positions=positions,
        total_unique_configurations=len(result['conditional'])+len(directions)+len(result['displacement'])+geometric,
        eligible_conditional=int(result['conditional'].search_eligible.sum()),eligible_directional=int(directions.search_eligible.sum()))
    return dict(**result,maxima=maxima,window_maxima=window_max,space=space,encoders=encoders)

def compare_frequency_nulls(x,config=FrequencySearchConfig(),*,replicates=199,seed=80042,progress=None):
    x=binary_matrix(x)
    if not np.all(x.sum(axis=1)==6) or type(replicates) is not int or replicates<1: raise ValueError('Valid Lotto rows and positive replicates required')
    observed=search_frequency(x,config,details=False);rows=[];follow=[]
    for kind,code in [('iid',0),('fixed_margins',1)]:
        for i in range(replicates):
            child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
            surrogate=iid_surrogate(len(x),seed=child) if kind=='iid' else constrained_surrogate(x,seed=child)
            r=search_frequency(surrogate,config,details=False)
            rows.append(dict(null_model=kind,replicate=i,seed=child,states_recomputed=True,encoder_refitted=True,
                **r['maxima'],**{f'{key}_W{window}':value for window,values in r['window_maxima'].items() for key,value in values.items()},
                **{'space_'+k:v for k,v in r['space'].items()}))
            f=r['conditional'].query('delta_draw==42 and delta_number==-5 and representation=="quantile"').copy()
            f['null_model']=kind;f['replicate']=i;follow.append(f)
            if progress and (i+1)%10==0: progress(f'{kind}: {i+1}/{replicates} COMPLETE all-window searches')
    null=pd.DataFrame(rows);comparison=[]
    for kind,group in null.groupby('null_model'):
        for stat,real in observed['maxima'].items():
            exceeds=int((group[stat]>=real).sum());p=(1+exceeds)/(replicates+1)
            comparison.append(dict(null_model=kind,statistic=stat,real_max=real,null_mean=float(group[stat].mean()),
                null_q95=float(group[stat].quantile(.95)),exceedances=exceeds,replicates=replicates,global_p=p,adjusted_p=min(1,5*p)))
    return pd.DataFrame(comparison),null,pd.concat(follow,ignore_index=True)
