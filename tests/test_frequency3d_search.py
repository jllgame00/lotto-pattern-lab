import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate,aligned

def test_conditional_counts_both_directions_zero_and_support():
    from src.analysis.frequency_search import conditional_frequency
    x=iid_surrogate(70,seed=17); states=np.tile(np.arange(45)%3,(70,1));states[:10]=-1
    table=conditional_frequency(x,states,state_count=3,max_dt=3,max_dn=2,min_support=1000)
    assert len(table)==3*3*5
    for row in table.itertuples():
        a,b=aligned(x,row.delta_draw,row.delta_number);s,_=aligned(states,row.delta_draw,row.delta_number)
        valid=a&(s==row.state)
        assert row.valid_opportunities==valid.sum() and row.matches==(valid&b).sum()
    assert not table.search_eligible.any()

@pytest.mark.parametrize('dn',[3,-3])
def test_planted_same_frequency_chain(dn):
    from src.analysis.frequency3d import frequency_states,FrequencyEncoder
    from src.analysis.frequency_search import search_frequency,FrequencySearchConfig
    x=np.zeros((70,45),bool)
    for i in range(5): x[20+3*i,(1 if dn>0 else 30)+dn*i]=True
    r=search_frequency(x,FrequencySearchConfig(max_dt=3,max_dn=3,trajectory_dt=3,trajectory_dn=3,min_support=1,chain_support=1))
    p=r['paths'].query('window==10 and kind=="same_bin" and delta_draw==3 and delta_number==@dn and start_draw==21')
    assert len(p)==1 and p.iloc[0].chain_length==5 and not p.iloc[0].overlaps_longer

def test_null_recomputes_frequency_and_global_max_deterministically():
    from src.analysis.frequency_search import search_frequency,compare_frequency_nulls,FrequencySearchConfig
    from src.analysis.spatiotemporal import constrained_surrogate
    cfg=FrequencySearchConfig(max_dt=2,max_dn=2,trajectory_dt=2,trajectory_dn=2,min_support=5,chain_support=2)
    x=iid_surrogate(65,seed=13);a,n,f=compare_frequency_nulls(x,cfg,replicates=2,seed=11)
    detailed=search_frequency(x,cfg,details=True);lean=search_frequency(x,cfg,details=False)
    assert detailed['maxima']==lean['maxima'] and detailed['space']==lean['space']
    assert detailed['window_maxima']==lean['window_maxima']
    a2,n2,f2=compare_frequency_nulls(x,cfg,replicates=2,seed=11)
    assert n.equals(n2) and a.equals(a2)
    for row in n.itertuples():
        s=iid_surrogate(len(x),seed=row.seed) if row.null_model=='iid' else constrained_surrogate(x,seed=row.seed)
        r=search_frequency(s,cfg,details=False)
        assert all(getattr(row,k)==v for k,v in r['maxima'].items())
    for row in a.itertuples():
        assert row.global_p==pytest.approx((1+(n[n.null_model==row.null_model][row.statistic]>=row.real_max).sum())/3)
        assert row.adjusted_p==min(1,5*row.global_p)

def test_direction_normalizes_opportunities_and_search_count():
    from src.analysis.frequency_search import search_frequency,FrequencySearchConfig
    r=search_frequency(iid_surrogate(65,seed=2),FrequencySearchConfig(max_dt=2,max_dn=2,trajectory_dt=2,trajectory_dn=2))
    assert r['space']['conditional']==109*2*5
    assert r['space']['directional']==109*2*2+3*2*2
    assert r['displacement'].usage.eq('DESCRIPTIVE_ONLY').all()
    assert set(r['conditional'].window)=={10,26,52}
