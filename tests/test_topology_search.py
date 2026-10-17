import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def module():
    from src.analysis import topology_search
    return topology_search


@pytest.mark.parametrize('n,cells,clouds,rolling',[(1245,560,140,27),(900,380,95,18)])
def test_exact_search_and_point_count_inventory(n,cells,clouds,rolling):
    raw=module().metric_vector(iid_surrogate(n,seed=23),details=False)
    assert len(raw['keys'])==len(set(raw['keys']))==cells
    assert raw['space']['clouds']==clouds and raw['space']['rolling_fits']==rolling
    assert all(v==clouds for v in raw['space']['family_cells'].values())
    assert raw['space']['point_counts'][:5]==[n,n,n,n//26,n//52]


def test_nulls_rebuild_identical_cloud_sizes_and_select_their_own_maxima():
    m=module();x=iid_surrogate(208,seed=3);c=m.fit_calibration(208,replicates=4,seed=2311)
    raw=m.metric_vector(x);real=m.complete_search(raw,c)
    a=m.null_search(x,{208:c},replicates=2,seed=2322,include_development=False)
    b=m.null_search(x,{208:c},replicates=2,seed=2322,include_development=False)
    for u,v in zip(a,b):
        entry=u['full'];assert entry['space']==real['space'] and entry['rebuilt']
        assert entry['representation_hash']!=raw['representation_hash']
        np.testing.assert_array_equal(entry['raw_values'],v['full']['raw_values'])
        assert m.complete_search(dict(raw,values=entry['raw_values']),c)['maxima']==entry['maxima']
        if u['null_model']=='fixed_margins':assert entry['fixed_margins_preserved']
    for row in m.compare_maxima(real,a):
        null=[r['full']['maxima'][row['family']] for r in a if r['null_model']==row['null_model']]
        p=(1+sum(v>=real['maxima'][row['family']] for v in null))/3
        assert row['global_p']==p and row['adjusted_p']==min(1,4*p)


def test_entropy_is_two_sided_and_constant_pilot_cells_are_not_tested():
    m=module();raw=dict(draws=208,keys=['a','b','c'],families=['h0_entropy','h0_entropy','h0_longest'],values=np.array([7.,3.,99.]))
    c=dict(draws=208,keys=raw['keys'],mean=np.array([5.,5.,5.]),std=np.array([1.,1.,0.]),eligible=np.array([True,True,False]))
    result=m.standardize(raw,c)
    np.testing.assert_array_equal(result[:2],[2.,2.]);assert np.isnan(result[2])


def test_parallel_seeds_equal_serial_searches():
    m=module();x=iid_surrogate(208,seed=4);c=m.fit_calibration(208,replicates=4,seed=2312)
    a=m.null_search(x,{208:c},replicates=1,workers=1,include_development=False)
    b=m.null_search(x,{208:c},replicates=1,workers=2,include_development=False)
    for u,v in zip(a,b):
        np.testing.assert_array_equal(u['full']['raw_values'],v['full']['raw_values'])
        assert u['full']['maxima']==v['full']['maxima']


def test_development_selection_cannot_use_later_or_create_predictor_from_structure_alone():
    m=module();x=iid_surrogate(900,seed=9);raw=m.metric_vector(x,details=False)
    c=dict(draws=900,keys=raw['keys'],mean=np.zeros(len(raw['keys'])),std=np.ones(len(raw['keys'])),eligible=np.ones(len(raw['keys']),bool))
    rows=[dict(null_model=k,development=dict(maxima={f:1e9 for f in m.FAMILIES})) for k in ('iid','fixed_margins') for _ in range(199)]
    result=m.development_selection(x,c,rows)
    assert not result['predictive_model_justified'] and result['decision']=='PREDICTIVE_MODEL_NOT_JUSTIFIED'
    for r in rows:r['development']['maxima']={f:-1e9 for f in m.FAMILIES}
    assert not m.development_selection(x,c,rows)['predictive_model_justified']
    with pytest.raises(ValueError):m.development_selection(iid_surrogate(901,seed=9),c,rows)
    with pytest.raises(ValueError):m.metric_vector(iid_surrogate(1246,seed=9))
    with pytest.raises(ValueError):m.complete_search(raw,dict(c,draws=1245))
