import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.analysis.information_search import complete_search,null_search,compare_maxima,FAMILIES


def test_complete_search_uses_own_global_max_and_equal_space():
    x=iid_surrogate(960,seed=12)
    args=dict(lags=(1,3),histories=((1,1),))
    r=complete_search(x,**args)
    assert r['space']['mi_cross']==45*44*2
    assert r['space']['te']==45*44*2
    assert r['space']['self_mi']==45*2
    assert r['maxima']['mi']==max(row['value'] for row in r['mi_rows'] if row['source']!=row['target'])
    rows=null_search(x,replicates=2,search_args=args,seed=130042)
    assert len(rows)==4 and all(row['space']==r['space'] for row in rows)
    assert len({row['representation_hash'] for row in rows})==4
    assert rows==null_search(x,replicates=2,search_args=args,seed=130042)


def test_global_p_has_plus_one_ties_and_five_family_correction():
    real={'maxima':dict.fromkeys(FAMILIES,2.)}
    rows=[dict(null_model=k,**dict.fromkeys(FAMILIES,v)) for k in ('iid','fixed_margins') for v in (1.,2.,3.)]
    compared=compare_maxima(real,rows)
    assert len(compared)==10 and all(r['global_p']==.75 and r['adjusted_p']==1 for r in compared)


def test_no1246_and_too_short_stability():
    with pytest.raises(ValueError):complete_search(iid_surrogate(1246,seed=1))
    with pytest.raises(ValueError):complete_search(iid_surrogate(300,seed=1))


def test_circular_shift_preserves_each_margin_and_target_history():
    from src.analysis.information_search import shifted_sources,temporal_randomization
    x=iid_surrogate(960,seed=5)
    shifts=shifted_sources(x,replicates=3,seed=8)
    assert all(np.array_equal(s.sum(0),x.sum(0)) for s in shifts)
    assert all(not np.array_equal(s,x) for s in shifts)
    assert all(np.array_equal(a,b) for a,b in zip(shifts,shifted_sources(x,replicates=3,seed=8)))
    result=temporal_randomization(x,replicates=3,lags=(1,),histories=((1,1),))
    assert result['replicates']==3
    assert result['mi_null'].shape==(3,1,45,45)
    assert result['te_null'].shape==(3,1,45,45)


def test_stability_requires_each_era_direction_support_and_positive_minimum():
    from src.analysis.information_search import stable_evidence
    def era(forward=.04,reverse=.01,corrected=.02,eligible=True):
        return dict(raw=np.array([[0,forward],[reverse,0]]),
            corrected=np.array([[0,corrected],[.001,0]]),eligible=np.full((2,2),eligible))
    score,mask=stable_evidence([era(),era(),era()])
    assert score[0,1]==.02 and mask[0,1] and not mask[1,0]
    for bad in (era(eligible=False),era(forward=.001,reverse=.01),era(corrected=-.001)):
        score,mask=stable_evidence([era(),bad,era()])
        assert score[0,1]==0
