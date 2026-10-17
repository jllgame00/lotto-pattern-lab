"""Nine-state translations, explicit parent controls and complete-search nulls."""
from dataclasses import dataclass,asdict
import numpy as np
import pandas as pd
from src.analysis.joint_state import JointEncoder,LABELS
from src.analysis.frequency_search import conditional_frequency
from src.analysis.gap3d_search import statistics,_maximum
from src.analysis.spatiotemporal import binary_matrix,aligned,iid_surrogate,constrained_surrogate,P

@dataclass(frozen=True)
class JointSearchConfig:
    max_dt:int=52
    max_dn:int=15
    chain_dt:int=13
    chain_dn:int=6
    min_support:int=100
    chain_support:int=20
    prior:float=100.
    def __post_init__(self):
        ints=(self.max_dt,self.max_dn,self.chain_dt,self.chain_dn,self.min_support,self.chain_support)
        if any(type(v) is not int or v<1 for v in ints) or max(self.max_dn,self.chain_dn)>44 or not np.isfinite(self.prior) or self.prior<=0:
            raise ValueError('Valid positive bounded search configuration required')

def parent_controls(table,*,prior=100.,min_support=100):
    """Pool disjoint joint cells so every parent shares the same source universe."""
    if not np.isfinite(prior) or prior<=0: raise ValueError('Positive shrinkage prior required')
    table=table.copy();table['gap_state']=table.state//3;table['frequency_state']=table.state%3
    table['joint_label']=table.state.map(dict(enumerate(LABELS)))
    for label,keys in [('unconditional',[]),('gap',['gap_state']),('frequency',['frequency_state'])]:
        columns=keys+['delta_draw','delta_number']
        group=table.groupby(columns,as_index=False)[['source_observations','valid_opportunities','matches']].sum()
        group=group.rename(columns={'source_observations':label+'_sources','valid_opportunities':label+'_opportunities','matches':label+'_matches'})
        n,k=group[label+'_opportunities'],group[label+'_matches']
        group[label+'_rate']=np.divide(k,n,out=np.full(len(group),np.nan),where=n>0)
        group[label+'_shrunk_rate']=(k+prior*P)/(n+prior)
        table=table.merge(group,on=columns,validate='many_to_one')
    table['joint_shrunk_rate']=(table.matches+prior*P)/(table.valid_opportunities+prior)
    table['best_parent_shrunk_rate']=table[['gap_shrunk_rate','frequency_shrunk_rate']].max(axis=1)
    table['interaction_lift']=table.joint_shrunk_rate/table.best_parent_shrunk_rate-1
    table['interaction_difference']=table.joint_shrunk_rate-table.best_parent_shrunk_rate
    table['search_eligible']=(table.valid_opportunities>=min_support)&(table.gap_opportunities>=min_support)&(table.frequency_opportunities>=min_support)
    table['parent_scope']='same eligible pre-source population; both dimensions known'
    return table

def same_state_chains(x,states,*,max_dt=13,max_dn=6,min_support=20,details=True):
    x=binary_matrix(x);states=np.asarray(states)
    if states.shape!=x.shape: raise ValueError('State shape mismatch')
    rows=[];paths=[];longest=0
    for dt in range(1,max_dt+1):
        for dn in range(-max_dn,max_dn+1):
            if not dn: continue
            maximum=min((len(x)-1)//dt,44//abs(dn))+1
            for state in range(9):
                allowed=states==state;active=x&allowed;lengths=active.astype(np.int16) if details else None
                for length in range(2,maximum+1):
                    step=length-1;a,b=aligned(x,dt,dn,step);tlen,nlen=a.shape;offset=max(0,-step*dn)
                    eligible=active[:tlen,offset:offset+nlen]&aligned(allowed,dt,dn,step)[1]
                    continued=eligible&b;count=int(continued.sum())
                    if length in (3,4,5): rows.append(dict(state=state,delta_draw=dt,delta_number=dn,chain_length=length,
                        valid_opportunities=int(eligible.sum()),matches=count,geometric_starts=(len(x)-step*dt)*(45-step*abs(dn))))
                    active=np.zeros_like(x);active[:tlen,offset:offset+nlen]=continued
                    if count:
                        if length>=3:longest=max(longest,length)
                        if details:lengths[active]=length
                    elif length>=5:break
                if not details:continue
                predecessor=np.zeros_like(x);a,_=aligned(x,dt,dn);previous=a&aligned(allowed,dt,dn)[0]
                if dn>0:predecessor[dt:,dn:]=previous
                else:predecessor[dt:,:45+dn]=previous
                ts,ns=np.where((lengths>=3)&~predecessor)
                for t,n in zip(ts,ns):
                    length=int(lengths[t,n]);geom=min((len(x)-1-t)//dt,(44-n)//dn if dn>0 else n//(-dn))+1
                    paths.append(dict(state=state,label=LABELS[state],start_draw=int(t+1),start_number=int(n+1),
                        delta_draw=dt,delta_number=dn,chain_length=length,support=length,geometric_maximum=int(geom),
                        end_draw=int(t+1+(length-1)*dt),end_number=int(n+1+(length-1)*dn),overlaps_longer=False,
                        nested_fragments_suppressed=(length-1)*(length-2)//2-1))
    counts=pd.DataFrame(rows)
    return statistics(counts,min_support) if len(counts) else counts,pd.DataFrame(paths),longest

def chain_geometry(length,config):
    tuples=0;positions=0
    for dt in range(1,config.chain_dt+1):
        for dn in range(1,config.chain_dn+1):
            maximum=min((length-1)//dt,44//dn)+1
            tuples+=18*max(0,maximum-2)
            positions+=18*sum((length-step*dt)*(45-step*dn) for step in range(2,maximum))
    return int(tuples),int(positions)

def search_joint(x,config=JointSearchConfig(),*,details=True):
    x=binary_matrix(x)
    if len(x)<=max(26,config.max_dt,config.chain_dt):raise ValueError('Insufficient bounded history')
    encoder=JointEncoder().fit(x,cutoff=len(x));states=encoder.transform(x)['joint_state'][:-1]
    table=parent_controls(conditional_frequency(x,states,state_count=9,max_dt=config.max_dt,max_dn=config.max_dn,
        min_support=config.min_support),prior=config.prior,min_support=config.min_support)
    chains,paths,longest=same_state_chains(x,states,max_dt=config.chain_dt,max_dn=config.chain_dn,min_support=config.chain_support,details=details)
    eligible=table.loc[table.search_eligible,'interaction_lift']
    maxima=dict(joint_conditional=_maximum(table),interaction_lift=max(0.,float(eligible.max())) if len(eligible) else 0.,
        chain_continuation=_maximum(chains),longest_chain=longest)
    geometry,positions=chain_geometry(len(x),config)
    space=dict(joint_translations=len(table),interaction_comparisons=len(table),
        parent_control_rows=7*config.max_dt*(2*config.max_dn+1),chain_length_3_4_5=len(chains),
        chain_all_geometric_lengths=geometry,chain_rule_length_start_positions=positions,
        total_searched_parameter_statistics=2*len(table)+geometry,
        eligible_joint_translations=int(table.search_eligible.sum()),eligible_chains=int(chains.search_eligible.sum()) if len(chains) else 0)
    return dict(translations=table,chains=chains,paths=paths,maxima=maxima,space=space,encoder=encoder.configuration())

def compare_joint_nulls(x,config=JointSearchConfig(),*,replicates=199,seed=90042,progress=None):
    x=binary_matrix(x)
    if not np.all(x.sum(axis=1)==6) or type(replicates) is not int or replicates<1:raise ValueError('Lotto rows and positive replicates required')
    observed=search_joint(x,config,details=False);rows=[]
    for kind,code in [('iid',0),('fixed_margins',1)]:
        for i in range(replicates):
            child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
            surrogate=iid_surrogate(len(x),seed=child) if kind=='iid' else constrained_surrogate(x,seed=child)
            r=search_joint(surrogate,config,details=False)
            rows.append(dict(null_model=kind,replicate=i,seed=child,gaps_recomputed=True,frequencies_recomputed=True,encoders_refitted=True,
                gap_edges=str(r['encoder']['gap']['quantile_edges']),frequency_edges=str(r['encoder']['frequency']['quantile_edges']),
                **r['maxima'],**{'space_'+k:v for k,v in r['space'].items()}))
            if progress and (i+1)%10==0:progress(f'{kind}: {i+1}/{replicates} complete joint-state searches')
    null=pd.DataFrame(rows);comparison=[]
    for kind,group in null.groupby('null_model'):
        for statistic,value in observed['maxima'].items():
            exceeds=int((group[statistic]>=value).sum());p=(exceeds+1)/(replicates+1)
            comparison.append(dict(null_model=kind,statistic=statistic,real_max=value,null_mean=float(group[statistic].mean()),
                null_q95=float(group[statistic].quantile(.95)),exceedances=exceeds,replicates=replicates,global_p=p,adjusted_p=min(1.,4*p)))
    return pd.DataFrame(comparison),null
