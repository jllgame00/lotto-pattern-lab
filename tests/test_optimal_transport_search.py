import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def test_complete_search_parity_rebuild_and_deterministic_nulls():
    from src.analysis.optimal_transport_search import metric_vector, fit_calibration, null_search, FAMILIES
    x=iid_surrogate(156,seed=17);c=fit_calibration(156,replicates=4)
    a=null_search(x,{156:c},replicates=2,include_development=False)
    b=null_search(x,{156:c},replicates=2,include_development=False)
    raw=metric_vector(x)
    assert len(raw['keys'])==len(set(raw['keys']))
    assert set(raw['families'])==set(FAMILIES)
    for one,two in zip(a,b):
        np.testing.assert_array_equal(one['full']['raw_values'],two['full']['raw_values'])
        assert one['full']['space']==raw['space']
        assert one['full']['rebuilt'] and one['full']['row_six']
        assert one['full']['representation_hash']!=raw['representation_hash']
        if one['null_model']=='fixed_margins': assert one['full']['fixed_margins_preserved']


def test_global_maxima_use_each_surrogates_own_strongest_cell():
    from src.analysis.optimal_transport_search import complete_search, compare_maxima, FAMILIES
    families=[f for f in FAMILIES for _ in range(2)]
    keys=[str(i) for i in range(12)]
    raw=dict(draws=130,keys=keys,families=families,metadata=[{}]*12,
             values=np.array([1,-4]*6),space={},representation_hash='real')
    c=dict(draws=130,keys=keys,mean=np.zeros(12),std=np.ones(12),eligible=np.ones(12,bool))
    observed=complete_search(raw,c)
    assert all(v==4 for v in observed['maxima'].values())
    raw['values']=np.array([5,-2]*6)
    null=complete_search(raw,c)
    assert all(v==5 for v in null['maxima'].values())
    rows=[dict(null_model=k,full=null) for k in ('iid','fixed_margins')]
    assert all(r['global_p']==1 and r['adjusted_p']==1 for r in compare_maxima(observed,rows))


def test_development_selection_rejects_later_rows():
    from src.analysis.optimal_transport_search import development_selection
    with pytest.raises(ValueError,match='900'):
        development_selection(iid_surrogate(901,seed=1),{},[])


def test_research_rejects_draw1246_without_truncation():
    from src.analysis.optimal_transport_search import metric_vector
    with pytest.raises(ValueError):metric_vector(iid_surrogate(1246,seed=1))


def test_null_raw_vectors_match_fresh_seeded_history_search():
    from src.analysis.optimal_transport_search import metric_vector,fit_calibration,null_search
    from src.analysis.spatiotemporal import constrained_surrogate
    x=iid_surrogate(156,seed=33);c=fit_calibration(156,replicates=4)
    rows=null_search(x,{156:c},replicates=1,include_development=False)
    for row in rows:
        seed=row['full']['seed']
        null=iid_surrogate(156,seed=seed) if row['null_model']=='iid' else constrained_surrogate(x,seed=seed)
        np.testing.assert_array_equal(metric_vector(null)['values'],row['full']['raw_values'])


def test_development_selection_ignores_full_scope_null_results():
    from src.analysis.optimal_transport_search import metric_vector,fit_calibration,complete_search,development_selection
    x=iid_surrogate(900,seed=49);c=fit_calibration(900,replicates=4)
    raw=metric_vector(x);found=complete_search(raw,c)
    rows=[dict(null_model=k,development=found,full={'maxima':{'successor':0}}) for k in ('iid','fixed_margins')]
    before=development_selection(x,c,rows)
    for row in rows:row['full']={'maxima':{'successor':1e12}}
    assert before==development_selection(x,c,rows)
    assert not before['predictive_model_justified']


def test_continuation_gate_rejects_positive_gains_below_null_expectation():
    from src.analysis.optimal_transport_search import metric_vector,development_selection,FAMILIES
    x=iid_surrogate(900,seed=49);raw=metric_vector(x)
    mean=raw['values'].copy()
    for i,key in enumerate(raw['keys']):
        if key.startswith('successor|') and ('cosine_gain' in key or 'distance_gain' in key):mean[i]+=8
    c=dict(draws=900,keys=raw['keys'],mean=mean,std=np.ones(len(mean)),eligible=np.ones(len(mean),bool))
    null=dict(maxima={f:0. for f in FAMILIES})
    rows=[dict(null_model=k,development=null) for k in ('iid','fixed_margins') for _ in range(199)]
    selection=development_selection(x,c,rows)
    assert 'successor' in selection['passing_families']
    assert not selection['continuation_gate_passed']
