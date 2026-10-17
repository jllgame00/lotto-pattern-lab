import numpy as np
import pytest

from src.analysis.long_memory_search import (metric_vector, fit_calibration,
    complete_search, null_search, compare_maxima, development_selection, FAMILIES)
from src.analysis.spatiotemporal import iid_surrogate


def test_complete_search_inventory_and_determinism():
    x=iid_surrogate(416,seed=21)
    a=metric_vector(x);b=metric_vector(x)
    assert a['keys']==b['keys']
    np.testing.assert_allclose(a['values'],b['values'],equal_nan=True)
    assert len(a['keys'])==len(set(a['keys']))==len(a['values'])
    assert set(a['families'])==set(FAMILIES)
    assert sum(a['space']['family_cells'].values())==len(a['keys'])
    assert a['space']['series']==55


def test_surrogates_rebuild_and_global_max_parity():
    # N=312 has only one scale above knot52 and no supported crossover.
    x=iid_surrogate(416,seed=3)
    c=fit_calibration(416,replicates=4,seed=4)
    real=complete_search(metric_vector(x),c)
    a=null_search(x,{416:c},replicates=2,seed=5,include_development=False)
    b=null_search(x,{416:c},replicates=2,seed=5,include_development=False)
    assert len(a)==4
    for u,v in zip(a,b):
        assert u['full']['space']==real['space']
        assert u['full']['representation_hash']!=real['representation_hash']
        np.testing.assert_allclose(u['full']['raw_values'],v['full']['raw_values'],equal_nan=True)
        independent=complete_search(dict(metric_vector(x),values=u['full']['raw_values']),c)
        assert u['full']['maxima']==independent['maxima']
    rows=compare_maxima(real,a)
    for row in rows:
        maxima=[z['full']['maxima'][row['family']] for z in a if z['null_model']==row['null_model']]
        expected=(1+sum(z>=real['maxima'][row['family']] for z in maxima))/3
        assert row['global_p']==expected
        assert row['adjusted_p']==min(1,row['correction_families']*expected)


def test_development_only_and_failed_gate():
    x=iid_surrogate(900,seed=8)
    rows=[dict(family=f,null_model=n,adjusted_p=1.) for f in FAMILIES
          for n in ('iid','fixed_margins')]
    a=development_selection(x,rows)
    assert a['training_cutoff']==900 and not a['predictive_model_justified']
    assert a['decision']=='PREDICTIVE_MODEL_NOT_JUSTIFIED'
    with pytest.raises(ValueError):development_selection(iid_surrogate(901,seed=8),rows)
    with pytest.raises(ValueError):metric_vector(np.vstack((x,x[:346])))


def test_calibration_cutoff_mismatch():
    c=fit_calibration(312,replicates=4,seed=6)
    with pytest.raises(ValueError):complete_search(metric_vector(iid_surrogate(416,seed=9)),c)


def test_gate_cannot_combine_passing_anti_family_with_unrelated_persistent_series():
    # Deliberately fabricated p-values isolate gate logic, not null inference.
    # Seed1's selected persistent band has stable fits in all three eras.
    x=iid_surrogate(900,seed=1)
    rows=[dict(family=f,null_model=n,adjusted_p=.03 if f=='anti_persistent' else 1.)
          for f in FAMILIES for n in ('iid','fixed_margins')]
    result=development_selection(x,rows)
    assert result['era_stable']
    assert result['passing_primary_families']==['anti_persistent']
    assert result['decision']=='PREDICTIVE_MODEL_NOT_JUSTIFIED'


def test_gate_requires_the_passing_winner_and_matching_direction():
    # Evidence is fabricated here solely to exercise conservative gate branches.
    x=iid_surrogate(900,seed=1)
    def rows(family):
        return [dict(family=f,null_model=n,adjusted_p=.03 if f==family else 1.)
                for f in FAMILIES for n in ('iid','fixed_margins')]
    wrong=development_selection(x,rows('persistent'),leaders={'persistent':{'series':'number_01'}})
    assert not wrong['predictive_model_justified']
    opposite=development_selection(x,rows('anti_persistent'),leaders={'anti_persistent':{'series':'band_10_18'}})
    assert opposite['era_stable'] and not opposite['predictive_model_justified']
    linked=development_selection(x,rows('persistent'),leaders={'persistent':{'series':'band_10_18'}})
    assert linked['linked_primary_families']==['persistent']
    assert linked['decision']=='REVIEW_PREDICTIVE_DESIGN'
