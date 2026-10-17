import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.analysis.change_point_search import (metric_vector,fit_calibration,standardize,complete_search,
    null_search,compare_maxima,stable_boundary,prefix_sizes,FAMILIES)


def test_fixed_search_count_and_prefixes():
    r=metric_vector(iid_surrogate(520,seed=19))
    assert len(r['keys'])==len(set(r['keys']))==2237
    assert r['space']['family_cells']==dict(single_number=585,global_shift=68,concentration=24,concordance=360,stability=1200)
    assert r['space']['units_per_prefix']==50 and r['space']['configurations_per_prefix']==300
    assert prefix_sizes(1245)==[800,900,1000,1100,1245]
    assert prefix_sizes(900)==[500,600,700,800,900]
    assert r['space']['prefixes']==[120,220,320,420,520]


@pytest.fixture(scope='module')
def calibration():return fit_calibration(520,replicates=4,seed=192900)


def test_global_max_own_search_and_calibration_cutoff(calibration):
    raw=metric_vector(iid_surrogate(520,seed=99));z=standardize(raw,calibration);found=complete_search(raw,calibration)
    for family in FAMILIES:
        assert found['maxima'][family]==pytest.approx(np.nanmax(z[np.array(raw['families'])==family]))
    with pytest.raises(ValueError):standardize(raw,dict(calibration,draws=900))
    with pytest.raises(ValueError):standardize(dict(raw,keys=raw['keys'][::-1]),calibration)


def test_complete_null_rebuild_determinism_and_family_correction(calibration):
    x=iid_surrogate(520,seed=101)
    a=null_search(x,{520:calibration},replicates=1,include_development=False)
    b=null_search(x,{520:calibration},replicates=1,include_development=False)
    real=complete_search(metric_vector(x),calibration)
    for first,second in zip(a,b):
        assert first['rebuilt'] and first['full']['space']==real['space']
        assert first['full']['representation_hash']!=real['representation_hash']
        np.testing.assert_array_equal(first['full']['raw_values'],second['full']['raw_values'])
    c=compare_maxima(real,a,scope='full');assert len(c)==10
    assert all(r['global_p']>=.5 and r['adjusted_p']==min(1,5*r['global_p']) for r in c)


def test_stability_requires_earlier_support_and_real_matching_boundaries():
    full=dict(boundaries=[300],boundary_gains=[15.],proposal_boundary=300,proposal_gain=10.,penalty=5.,minimum=26,used_draws=1245)
    past=[dict(full,used_draws=n) for n in (800,900,1000,1100)]
    r=stable_boundary(full,past,tolerance=13,kind='detected')
    assert r['score']==3. and r['matches']==4 and r['boundary']==300
    assert stable_boundary(dict(full,boundaries=[]),past,tolerance=13,kind='detected')['score']==0
    assert stable_boundary(full,past[:1],tolerance=13,kind='detected')['score']==0
    moved=[dict(p,boundaries=[600],proposal_boundary=600) for p in past]
    assert stable_boundary(full,moved,tolerance=13,kind='proposal')['score']==0


def test_constant_history_has_no_arbitrary_proposal_evidence():
    x=np.zeros((520,45),dtype=bool);x[:,:6]=True
    r=metric_vector(x)
    for family in ('single_number','global_shift','concentration','concordance','stability'):
        assert np.allclose(r['values'][np.array(r['families'])==family],0)


def test_future_history_and_insufficient_pilot_are_rejected():
    with pytest.raises(ValueError):metric_vector(np.vstack([iid_surrogate(1245,seed=1),iid_surrogate(2,seed=2)[0]]))
    with pytest.raises(ValueError):fit_calibration(520,replicates=1)
