import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def module():
    from src.analysis import random_matrix_search
    return random_matrix_search


@pytest.mark.parametrize('n,cells,rolling,stability',[(1245,2443,39,372),(900,1699,27,228)])
def test_exact_predeclared_inventory(n,cells,rolling,stability):
    raw=module().metric_vector(iid_surrogate(n,seed=22))
    assert len(raw['keys'])==len(set(raw['keys']))==cells
    assert raw['space']['rolling_fits']==rolling
    assert raw['space']['family_cells']['stability']==stability
    assert raw['space']['ranks']==[1,2,3,5]
    assert raw['space']['lags']==[1,2,4,8,13]
    assert raw['spectra'].shape==(rolling+4,2,44)
    assert raw['space']['primary_representation']=='correlation'


def test_every_surrogate_rebuilds_same_search_and_own_maxima():
    m=module();x=iid_surrogate(624,seed=5)
    c=m.fit_calibration(624,replicates=4,seed=2211)
    raw=m.metric_vector(x);real=m.complete_search(raw,c)
    a=m.null_search(x,{624:c},replicates=2,seed=2222,include_development=False)
    b=m.null_search(x,{624:c},replicates=2,seed=2222,include_development=False)
    assert len(a)==4
    for u,v in zip(a,b):
        entry=u['full'];assert entry['space']==real['space'] and entry['rebuilt']
        assert entry['representation_hash']!=raw['representation_hash']
        np.testing.assert_array_equal(entry['raw_values'],v['full']['raw_values'])
        np.testing.assert_array_equal(entry['spectra'],v['full']['spectra'])
        if u['null_model']=='fixed_margins':assert entry['fixed_margins_preserved']
        independent=m.complete_search(dict(raw,values=entry['raw_values']),c)
        assert independent['maxima']==entry['maxima']
    for row in m.compare_maxima(real,a):
        null=[r['full']['maxima'][row['family']] for r in a if r['null_model']==row['null_model']]
        p=(1+sum(v>=real['maxima'][row['family']] for v in null))/3
        assert row['global_p']==p and row['adjusted_p']==min(1,6*p)


def test_worker_count_does_not_change_seeded_results():
    m=module();x=iid_surrogate(416,seed=5);c=m.fit_calibration(416,replicates=4,seed=2212)
    a=m.null_search(x,{416:c},replicates=1,include_development=False,workers=1)
    b=m.null_search(x,{416:c},replicates=1,include_development=False,workers=2)
    for u,v in zip(a,b):
        np.testing.assert_array_equal(u['full']['raw_values'],v['full']['raw_values'])
        assert u['full']['maxima']==v['full']['maxima']


def test_development_selection_cannot_take_later_history_or_unrelated_winner():
    m=module();x=iid_surrogate(900,seed=91);c=m.fit_calibration(900,replicates=4,seed=2213)
    raw=m.metric_vector(x);actual=m.complete_search(raw,c)
    # All six family extrema deliberately dominate real evidence: no gate.
    rows=[dict(null_model=k,development=dict(maxima={f:100. for f in m.FAMILIES}))
          for k in ('iid','fixed_margins') for _ in range(199)]
    selection=m.development_selection(x,c,rows)
    assert not selection['predictive_model_justified']
    assert selection['decision']=='PREDICTIVE_MODEL_NOT_JUSTIFIED'
    with pytest.raises(ValueError):m.development_selection(iid_surrogate(901,seed=91),c,rows)
    with pytest.raises(ValueError):m.complete_search(raw,dict(c,draws=1245))
    with pytest.raises(ValueError):m.metric_vector(iid_surrogate(1246,seed=91))
    assert actual['leaders']['largest']['location'] in ('whole','rolling')


def test_rolling_fit_uses_only_its_own_interval():
    from src.analysis.random_matrix import fit_matrix
    m=module();x=iid_surrogate(624,seed=92);raw=m.metric_vector(x)
    first=next(r for r in raw['intervals'] if r['location']=='rolling' and r['window']==104 and r['end']==104)
    np.testing.assert_array_equal(first['correlation']['matrix'],fit_matrix(x[:104])['matrix'])
    altered=x.copy();altered[104:]=iid_surrogate(520,seed=93)
    second=m.metric_vector(altered)
    matched=next(r for r in second['intervals'] if r['location']=='rolling' and r['window']==104 and r['end']==104)
    np.testing.assert_array_equal(first['correlation']['matrix'],matched['correlation']['matrix'])


def test_unrelated_significant_rolling_winners_cannot_rescue_development_gate():
    m=module();x=iid_surrogate(900,seed=94);raw=m.metric_vector(x)
    # Artificial centering creates z=10 at unrelated rolling cells, z=0 at
    # the required whole/era-min cells. It is a gate fixture, not inference.
    c=dict(draws=900,keys=raw['keys'],mean=raw['values'].copy(),std=np.ones(len(raw['keys'])),eligible=np.ones(len(raw['keys']),bool))
    for family in ('largest','stability'):
        i=next(i for i,meta in enumerate(raw['metadata']) if meta['family']==family and meta['location'] in ('rolling','rolling_pair'))
        c['mean'][i]-=10
    rows=[dict(null_model=k,development=dict(maxima={f:5. for f in m.FAMILIES})) for k in ('iid','fixed_margins') for _ in range(199)]
    found=m.complete_search(raw,c)
    assert found['maxima']['largest']==pytest.approx(10) and found['maxima']['stability']==pytest.approx(10)
    for whole_passes in (False,True):
        if whole_passes:c['mean'][raw['keys'].index('largest|whole|0|900')]-=10
        result=m.development_selection(x,c,rows)
        assert result['whole_leading_mode_passed']==whole_passes
        assert result['stable_ranks']==[] and not result['predictive_model_justified']
