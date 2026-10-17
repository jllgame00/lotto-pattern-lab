import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.analysis.symmetry_search import (metric_vector,fit_calibration,standardize,complete_search,
    null_search,compare_maxima,FAMILIES)


def test_predeclared_space_and_no_pair_selection_shortcut():
    raw=metric_vector(iid_surrogate(260,seed=18))
    assert len(raw['keys'])==len(set(raw['keys']))==3406
    assert raw['space']['family_cells']==dict(same_draw=4,pooled=9,pair=1518,asymmetry=198,regime=104,anti=1528,shift=45)
    assert raw['space']['mirror_pairs']==22 and raw['space']['activity_correlations']==1122
    assert raw['space']['regime_windows']==26
    assert all(m.get('source')!=23 for m in raw['metadata'])


@pytest.fixture(scope='module')
def calibration():return fit_calibration(260,replicates=6,seed=182900)


def test_own_global_max_and_length_key_identity(calibration):
    raw=metric_vector(iid_surrogate(260,seed=99));z=standardize(raw,calibration);result=complete_search(raw,calibration)
    for family in FAMILIES:
        mask=np.array(raw['families'])==family
        assert result['maxima'][family]==pytest.approx(np.nanmax(z[mask]))
        assert result['leaders'][family]['key'] in raw['keys']
    with pytest.raises(ValueError):standardize(raw,dict(calibration,draws=900))
    with pytest.raises(ValueError):standardize(dict(raw,keys=raw['keys'][::-1]),calibration)


def test_deterministic_complete_surrogate_search(calibration):
    x=iid_surrogate(260,seed=101)
    a=null_search(x,{260:calibration},replicates=2,include_development=False)
    b=null_search(x,{260:calibration},replicates=2,include_development=False)
    real=complete_search(metric_vector(x),calibration)
    assert len(a)==4
    for first,second in zip(a,b):
        assert first['rebuilt']
        assert first['full']['space']==real['space']
        assert first['full']['representation_hash']!=real['representation_hash']
        np.testing.assert_array_equal(first['full']['raw_values'],second['full']['raw_values'])
    comparison=compare_maxima(real,a,scope='full');assert len(comparison)==14
    assert all(r['global_p']>=1/3 and r['adjusted_p']==min(1,7*r['global_p']) for r in comparison)


def test_anti_sign_is_separate_and_secondary_shift_contains_zero_reference():
    raw=metric_vector(iid_surrogate(260,seed=102));lookup=dict(zip(raw['keys'],raw['values']))
    for m,value in zip(raw['metadata'],raw['values']):
        if m['family']=='anti' and m['kind']=='negative_pair_risk':
            key=f"pair_risk/lag={m['lag']},source={m['source']},target={m['target']}"
            assert value==pytest.approx(-lookup[key],nan_ok=True)
    assert sum(m['family']=='shift' and m['shift']==0 for m in raw['metadata'])==9


def test_fixed_margin_development_uses_own900_prefix(monkeypatch):
    from src.analysis import symmetry_search as module
    x=iid_surrogate(1245,seed=9);received=[]
    def constrained(actual,*,seed):received.append(actual.copy());return actual.copy()
    monkeypatch.setattr(module,'constrained_surrogate',constrained)
    monkeypatch.setattr(module,'metric_vector',lambda a,**k:dict(values=np.array([len(a)])))
    monkeypatch.setattr(module,'complete_search',lambda r,c:dict(cutoff=int(r['values'][0])))
    row=module._null_job(x,{1245:{},900:{}},'fixed_margins',1,0,42,True)
    assert [len(a) for a in received]==[1245,900]
    np.testing.assert_array_equal(received[1],x[:900]);assert row['development']['cutoff']==900


def test_phase18_future_and_sparse_calibration_are_rejected():
    with pytest.raises(ValueError):metric_vector(np.vstack([iid_surrogate(1245,seed=2),iid_surrogate(2,seed=3)[0]]))
    with pytest.raises(ValueError):fit_calibration(260,replicates=1)
