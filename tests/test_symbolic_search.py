import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate


def test_complete_search_inventory_surrogate_rebuilding_and_determinism():
    from src.analysis.symbolic_search import metric_vector,fit_calibration,null_search
    x=iid_surrogate(900,seed=31);c=fit_calibration(900,replicates=4)
    raw=metric_vector(x)
    assert len(raw['keys'])==len(set(raw['keys']))==304
    assert raw['space']['family_cells']==dict(entropy=24,heldout=48,transition=16,word=48,forbidden=80,run_lag=88)
    a=null_search(x,{900:c},replicates=1,include_development=False)
    b=null_search(x,{900:c},replicates=1,include_development=False)
    for one,two in zip(a,b):
        entry=one['full'];np.testing.assert_array_equal(entry['raw_values'],two['full']['raw_values'])
        assert entry['rebuilt'] and entry['space']==raw['space'] and entry['row_six']
        null=iid_surrogate(900,seed=entry['seed']) if one['null_model']=='iid' else constrained_surrogate(x,seed=entry['seed'])
        fresh=metric_vector(null)
        np.testing.assert_array_equal(fresh['values'],entry['raw_values'])
        assert fresh['encoding_hash']==entry['encoding_hash']!=raw['encoding_hash']
        if one['null_model']=='fixed_margins':assert entry['fixed_margins_preserved']


def test_each_history_selects_its_own_global_max_and_correction():
    from src.analysis.symbolic_search import complete_search,compare_maxima,FAMILIES
    keys=[str(i) for i in range(12)]
    raw=dict(draws=900,keys=keys,families=[f for f in FAMILIES for _ in range(2)],metadata=[{}]*12,
        values=np.array([1.,4.]*6),space={},representation_hash='x',encoding_hash='e')
    c=dict(draws=900,keys=keys,mean=np.zeros(12),std=np.ones(12),eligible=np.ones(12,bool))
    real=complete_search(raw,c);assert all(v==4 for v in real['maxima'].values())
    raw['values']=np.array([5.,2.]*6);null=complete_search(raw,c)
    rows=[dict(null_model=k,full=null) for k in ('iid','fixed_margins')]
    assert all(r['global_p']==r['adjusted_p']==1 for r in compare_maxima(real,rows))


def test_development_only_selection_and_no_future_research():
    from src.analysis.symbolic_search import development_selection,metric_vector
    with pytest.raises(ValueError,match='900'):development_selection(iid_surrogate(901,seed=1),{},[])
    with pytest.raises(ValueError):metric_vector(iid_surrogate(1246,seed=1))


def test_constant_pilot_cells_are_retained_with_fixed_fallback_scale():
    from src.analysis.symbolic_search import fit_calibration
    c=fit_calibration(900,replicates=4)
    assert c['eligible'].all() and len(c['eligible'])==304
    assert np.isfinite(c['std']).all() and (c['std']>0).all()


def test_development_choice_does_not_read_later_scope_nulls():
    from src.analysis.symbolic_search import fit_calibration,metric_vector,complete_search,development_selection
    x=iid_surrogate(900,seed=9);c=fit_calibration(900,replicates=4)
    found=complete_search(metric_vector(x),c)
    rows=[dict(null_model=kind,development=found,full={'unrelated':0}) for kind in ('iid','fixed_margins')]
    first=development_selection(x,c,rows)
    for row in rows:row['full']={'unrelated':1e90}
    assert first==development_selection(x,c,rows)
    assert not first['predictive_model_justified']
