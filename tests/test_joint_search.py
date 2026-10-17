import numpy as np
import pandas as pd
import pytest
from src.analysis.spatiotemporal import iid_surrogate,aligned

def test_joint_parent_controls_and_interaction_formula():
    from src.analysis.frequency_search import conditional_frequency
    from src.analysis.joint_search import parent_controls
    x=iid_surrogate(80,seed=7);states=np.tile(np.arange(45)%9,(80,1));states[:26]=-1
    table=parent_controls(conditional_frequency(x,states,state_count=9,max_dt=3,max_dn=2,min_support=5),min_support=5)
    for row in table.itertuples():
        a,b=aligned(x,row.delta_draw,row.delta_number);s,_=aligned(states,row.delta_draw,row.delta_number)
        for label,mask in [('unconditional',s>=0),('gap',(s>=0)&(s//3==row.state//3)),('frequency',(s>=0)&(s%3==row.state%3))]:
            valid=a&mask
            assert getattr(row,label+'_opportunities')==valid.sum()
            assert getattr(row,label+'_matches')==(valid&b).sum()
        assert row.interaction_lift==pytest.approx(row.joint_shrunk_rate/max(row.gap_shrunk_rate,row.frequency_shrunk_rate)-1)

@pytest.mark.parametrize('dn',[3,-3])
def test_planted_joint_interaction_and_chain(dn):
    from src.analysis.frequency_search import conditional_frequency
    from src.analysis.joint_search import parent_controls,same_state_chains
    x=np.zeros((60,45),bool);states=np.tile(np.arange(45)%9,(60,1));states[states==8]=0
    for i in range(5):
        t,n=20+3*i,(2 if dn>0 else 32)+i*dn;x[t,n]=True;states[t,n]=8
    # Other high-gap and HOT sources are deliberately unsuccessful controls.
    for t in range(3,17,2):x[t,16]=True;states[t,16]=6;x[t,40]=True;states[t,40]=2
    table=parent_controls(conditional_frequency(x,states,state_count=9,max_dt=3,max_dn=3,min_support=1),min_support=1)
    selected=table.query('state==8 and delta_draw==3 and delta_number==@dn').iloc[0]
    assert selected.interaction_lift>0
    counts,paths,longest=same_state_chains(x,states,max_dt=3,max_dn=3,min_support=1)
    path=paths.query('state==8 and delta_draw==3 and delta_number==@dn and start_draw==21')
    assert len(path)==1 and path.iloc[0].chain_length==5 and not path.iloc[0].overlaps_longer

def test_null_recomputes_both_dimensions_and_complete_maxima():
    from src.analysis.joint_search import search_joint,compare_joint_nulls,JointSearchConfig
    from src.analysis.spatiotemporal import constrained_surrogate
    cfg=JointSearchConfig(max_dt=2,max_dn=2,chain_dt=2,chain_dn=2,min_support=5,chain_support=2)
    x=iid_surrogate(65,seed=6);a,n=compare_joint_nulls(x,cfg,replicates=2,seed=9)
    a2,n2=compare_joint_nulls(x,cfg,replicates=2,seed=9)
    assert a.equals(a2) and n.equals(n2)
    real=search_joint(x,cfg);lean=search_joint(x,cfg,details=False)
    assert real['maxima']==lean['maxima'] and real['space']==lean['space']
    assert real['space']['joint_translations']==9*2*5
    for row in n.itertuples():
        s=iid_surrogate(len(x),seed=row.seed) if row.null_model=='iid' else constrained_surrogate(x,seed=row.seed)
        r=search_joint(s,cfg,details=False)
        assert all(getattr(row,k)==v for k,v in r['maxima'].items())
        assert row.gaps_recomputed and row.frequencies_recomputed and row.encoders_refitted
    for row in a.itertuples():
        assert row.global_p==pytest.approx((1+(n[n.null_model==row.null_model][row.statistic]>=row.real_max).sum())/3)
        assert row.adjusted_p==min(1,4*row.global_p)
