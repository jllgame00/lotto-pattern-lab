import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def test_frozen_family_inventory_and_track_b_removes_all_pure_margins():
    from src.analysis.randomness_battery import metric_vector,track_view
    x=iid_surrogate(1245,seed=41);raw=metric_vector(x)
    assert len(raw['keys'])==len(set(raw['keys']))==2200
    assert raw['space']['family_units']==dict(marginal=51,serial=495,run_gap=225,overlap=35,
        shape_distribution=21,shape_temporal=108,relational=992,spacing=47,spectral_entropy=226)
    b=track_view(raw,'fixed_margins')
    assert len(b['keys'])==2147 and 'marginal' not in b['families']
    assert 'shape_distribution|sum|mean' not in b['keys']
    assert 'shape_distribution|odd_count|mean' not in b['keys']
    assert 'shape_distribution|sum|variance' in b['keys']
    assert np.isfinite(raw['values']).all()


def test_era_slicing_is_nonoverlapping_and_frozen_battery_rebuilds():
    from src.analysis.randomness_battery import scope_histories,metric_vector
    x=iid_surrogate(1245,seed=13);scopes=scope_histories(x)
    assert list(scopes)==['full','early','middle','recent']
    np.testing.assert_array_equal(np.vstack([scopes[k] for k in ('early','middle','recent')]),x)
    raw=metric_vector(scopes['early'])
    assert len(raw['values'])==2200 and raw['details']['triple_support']['eligible']==0
    with pytest.raises(ValueError):scope_histories(iid_surrogate(1246,seed=2))


def test_all_nine_families_detect_controlled_nonrandom_history():
    from src.analysis.randomness_battery import metric_vector
    x=np.zeros((100,45),bool);x[:,:6]=True
    raw=metric_vector(x);d=dict(zip(raw['keys'],raw['values']))
    assert d['marginal|chi_square']>1000
    assert d['run_gap|number01|appearance']==100
    assert d['overlap|lag1|mean']==6
    assert d['relational|pair_01_02']==100
    assert d['spacing|difference01']==500
    assert d['shape_distribution|sum|mean']==21
    assert all(np.isfinite(v) for v in d.values())
