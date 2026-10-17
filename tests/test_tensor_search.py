import numpy as np
import pytest

from src.analysis.spatiotemporal import iid_surrogate
from src.analysis.tensor_search import (metric_vector, fit_calibration, standardize,
    complete_search, null_search, compare_maxima, choose_development, development_gate)


def test_exact_complete_search_space():
    r=metric_vector(iid_surrogate(130,seed=17))
    assert len(r['keys'])==len(set(r['keys']))==165
    assert r['space']['tucker_configurations']==36
    assert r['space']['family_cells']==dict(concentration=36,reconstruction=36,effective_rank=9,stability=36,temporal=48)
    assert np.isfinite(r['values']).all()
    assert r['dimensions']=={'A':[104,45,7],'B':[79,45,3],'C':[79,45,4]}


@pytest.fixture(scope='module')
def calibration():
    return fit_calibration(130,replicates=6,seed=171900)


def test_global_max_includes_own_strongest_cell(calibration):
    raw=metric_vector(iid_surrogate(130,seed=99))
    z=standardize(raw,calibration);result=complete_search(raw,calibration)
    for family in result['maxima']:
        mask=np.array(raw['families'])==family
        assert result['maxima'][family]==pytest.approx(np.nanmax(z[mask]))
        assert result['leaders'][family]['key'] in raw['keys']
    broken=dict(raw,keys=raw['keys'][::-1])
    with pytest.raises(ValueError):standardize(broken,calibration)


def test_deterministic_null_rebuild_and_parity(calibration):
    x=iid_surrogate(130,seed=19)
    first=null_search(x,{130:calibration},replicates=2,include_development=False)
    second=null_search(x,{130:calibration},replicates=2,include_development=False)
    real=complete_search(metric_vector(x),calibration)
    assert len(first)==4
    for a,b in zip(first,second):
        assert a['rebuilt']
        assert a['full']['space']==real['space']
        np.testing.assert_array_equal(a['full']['raw_values'],b['full']['raw_values'])
        assert a['full']['representation_hash']!=real['representation_hash']
    result=compare_maxima(real,first,scope='full')
    assert len(result)==10
    for row in result:
        assert row['global_p']>=1/3
        assert row['adjusted_p']==min(1,5*row['global_p'])


def test_development_only_selection(calibration):
    raw=metric_vector(iid_surrogate(130,seed=8))
    with pytest.raises(ValueError):choose_development(raw,standardize(raw,calibration))
    rows=[dict(null_model=n,family=f,adjusted_p=1.) for n in ('iid','fixed_margins')
          for f in ('concentration','reconstruction','effective_rank','stability','temporal')]
    assert development_gate(rows,cutoff=900)['predictive_model_justified'] is False
    with pytest.raises(ValueError):development_gate(rows,cutoff=1245)


def test_no_phase17_1246():
    with pytest.raises(ValueError):metric_vector(iid_surrogate(1245,seed=9).tolist()+[iid_surrogate(2,seed=4)[0].tolist()])


def test_sparse_calibration_rejects_and_no_degenerate_evidence():
    with pytest.raises(ValueError):fit_calibration(130,replicates=1)
    r=metric_vector(iid_surrogate(130,seed=27))
    c=dict(keys=r['keys'],mean=r['values'],std=np.zeros(165),eligible=np.zeros(165,dtype=bool))
    with pytest.raises(ValueError):complete_search(r,c)


def test_development_fixed_margin_uses_exact_own_prefix(monkeypatch):
    from src.analysis import tensor_search as module
    x=iid_surrogate(1245,seed=71);received=[]
    def constrained(actual,*,seed):
        received.append(actual.copy())
        return actual.copy()
    def metric(actual,**kwargs):return dict(values=np.array([len(actual)]))
    monkeypatch.setattr(module,'constrained_surrogate',constrained)
    monkeypatch.setattr(module,'metric_vector',metric)
    monkeypatch.setattr(module,'complete_search',lambda raw,c:dict(cutoff=int(raw['values'][0])))
    result=module._null_job(x,{1245:{},900:{}},'fixed_margins',1,0,42,True)
    assert [len(a) for a in received]==[1245,900]
    np.testing.assert_array_equal(received[1],x[:900])
    assert result['development']['cutoff']==900


def test_development_gate_requires_both_nulls_and_stability():
    rows=[dict(null_model=n,family=f,adjusted_p=1.) for n in ('iid','fixed_margins') for f in
          ('concentration','reconstruction','effective_rank','stability','temporal')]
    for row in rows:
        if row['family']=='reconstruction':row['adjusted_p']=.025
    assert not development_gate(rows,cutoff=900)['forecast_review_eligible']
    for row in rows:
        if row['family']=='stability':row['adjusted_p']=.025
    gate=development_gate(rows,cutoff=900)
    assert gate['forecast_review_eligible'] and not gate['predictive_model_justified']
    assert gate['status']=='FORECAST_REVIEW_REQUIRED'
    with pytest.raises(ValueError):development_gate(rows+[rows[0]],cutoff=900)


def test_development_choice_copies_spec_and_breaks_ties_deterministically():
    raw=dict(draws=900,keys=['first','second'],values=np.array([1.,2.]),metadata=[{'rank':2},{'rank':3}])
    choice=choose_development(raw,np.array([4.,4.]))
    assert choice['key']=='first'
    raw['metadata'][0]['rank']=6
    assert choice['spec']['rank']==2


def test_rank_deficient_history_excludes_arbitrary_nullspace_factors():
    x=np.zeros((104,45),dtype=bool);x[:,:6]=True
    raw=metric_vector(x)
    stability=np.array(raw['families'])=='stability'
    temporal=np.array(raw['families'])=='temporal'
    # C's fixed-centred gap and appearance can span two number directions;
    # A/B are rank one. Only unsupported directions must be excluded.
    invalid=np.array([m['tensor']!='C' or m.get('number_rank',0)>2 for m in raw['metadata']])
    assert np.isnan(raw['values'][stability&invalid]).all()
    assert np.isnan(raw['values'][temporal]).all()


def test_calibration_length_mismatch_is_rejected(calibration):
    raw=metric_vector(iid_surrogate(130,seed=6))
    with pytest.raises(ValueError,match='cutoff'):standardize(raw,dict(calibration,draws=1245))
