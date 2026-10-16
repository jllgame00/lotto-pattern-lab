import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate,aligned
from src.analysis.gap3d import causal_states,GapEncoder


def test_conditional_shift_matches_direct_and_sparse_guard():
    from src.analysis.gap3d_search import conditional_scores
    x=iid_surrogate(70,seed=17); g,m,r=causal_states(x)
    encoder=GapEncoder().fit(g[:-1],r[:-1],cutoff=70)
    states=encoder.transform(g[:-1],r[:-1])
    table=conditional_scores(x,states,state_count=3,max_dt=3,max_dn=2,min_support=1000)
    for row in table.itertuples():
        source,dest=aligned(x,row.delta_draw,row.delta_number)
        sg,_=aligned(states,row.delta_draw,row.delta_number)
        eligible=source&(sg==row.gap_state)
        assert row.valid_opportunities==eligible.sum()
        assert row.matches==(eligible&dest).sum()
    assert not table.search_eligible.any()


@pytest.mark.parametrize('dn,dg',[(3,2),(-3,-2)])
def test_planted_3d_trajectory_has_causal_gap_changes(dn,dg):
    from src.analysis.gap3d_search import trajectory_search
    x=np.zeros((50,45),bool)
    for i in range(5):
        draw,number,gap=20+i*3,(1 if dn>0 else 30)+i*dn,(2 if dg>0 else 10)+i*dg
        x[draw-1,number-1]=True; x[draw-gap-2,number-1]=True
    g,m,r=causal_states(x); enc=GapEncoder().fit(g[:-1],r[:-1],cutoff=50)
    state=enc.transform(g[:-1],r[:-1]); clipped=enc.transform(g[:-1],r[:-1],'clipped')
    counts,paths,maximum,space=trajectory_search(x,clipped,state,cap=enc.cap,max_dt=3,max_dn=3,delta_gap=2,details=True)
    p=paths.query('kind=="delta_gap" and delta_draw==3 and delta_number==@dn and rule==@dg and start_draw==20')
    assert len(p)==1 and p.iloc[0].chain_length==5 and p.iloc[0].start_gap==(2 if dg>0 else 10)
    assert not p.iloc[0].overlaps_longer and p.iloc[0].nested_fragments_suppressed>0
    assert maximum>=5


def test_global_search_recomputes_states_for_every_surrogate():
    from src.analysis.gap3d_search import Search3DConfig,search3d,compare_nulls3d
    x=iid_surrogate(60,seed=18)
    cfg=Search3DConfig(max_dt=3,max_dn=2,trajectory_dt=2,trajectory_dn=2,delta_gap=1,min_support=5,chain_support=2)
    real=search3d(x,cfg,details=False)
    assert set(real['maxima'])=={'conditional','destination','displacement','trajectory','longest_trajectory'}
    full=search3d(x,cfg,details=True)
    assert full['maxima']==real['maxima'] and full['search_space']==real['search_space']
    c,n,f=compare_nulls3d(x,cfg,replicates=2,seed=10)
    c2,n2,f2=compare_nulls3d(x,cfg,replicates=2,seed=10)
    assert n.equals(n2) and c.equals(c2)
    assert n.gap_recomputed.all() and n.encoder_refitted.all()
    from src.analysis.spatiotemporal import constrained_surrogate
    for row in n.itertuples():
        surrogate=iid_surrogate(len(x),seed=row.seed) if row.null_model=='iid' else constrained_surrogate(x,seed=row.seed)
        direct=search3d(surrogate,cfg,details=False)
        assert row.cap==direct['encoder']['clip_cap']
        assert all(getattr(row,key)==value for key,value in direct['maxima'].items())
    for row in c.itertuples():
        values=n[n.null_model==row.null_model][row.statistic]
        assert row.global_p==pytest.approx((1+(values>=row.real_max).sum())/3)
        assert row.adjusted_p==min(1,5*row.global_p)


def test_destination_outputs_are_marked_descriptive():
    from src.analysis.gap3d_search import search3d,Search3DConfig
    r=search3d(iid_surrogate(60,seed=42),Search3DConfig(max_dt=2,max_dn=2,trajectory_dt=2,trajectory_dn=2))
    assert r['destination'].usage.eq('DESCRIPTIVE_ONLY').all()
    assert r['displacement'].usage.eq('DESCRIPTIVE_ONLY').all()


def test_trajectory_search_space_includes_start_positions():
    from src.analysis.gap3d_search import trajectory_position_count,Search3DConfig
    cfg=Search3DConfig(max_dt=2,max_dn=1,trajectory_dt=1,trajectory_dn=1,delta_gap=1)
    expected=0
    for dn in (-1,1):
        # Three bin rules, plus gap changes -1,0,+1; cap2 limits nonzero changes.
        for maximum in (10,10,10,3,10,3):
            for length in range(3,maximum+1): expected+=(10-(length-1))*(45-(length-1)*abs(dn))
    assert trajectory_position_count(10,2,cfg)==expected
