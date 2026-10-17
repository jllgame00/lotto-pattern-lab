import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.analysis.transformed_search import complete_search,null_search,compare_maxima,FAMILIES


def test_complete_search_declared_space_and_maxima():
    x=iid_surrogate(140,seed=15);r=complete_search(x)
    assert r['space']['primary_cells']==1793
    assert r['space']['modular_structure_cells']==27 and r['space']['distance_cells']==308
    assert r['space']['modular_successor_cells']==1323
    assert set(r['maxima'])==set(FAMILIES) and all(np.isfinite(list(r['maxima'].values())))
    assert r['leaders']['distance']['distance'] in range(1,45)
    assert all(row['target_draw']<=140 for row in r['shape_rows'])


def test_global_max_surrogates_rebuild_and_determinism():
    x=iid_surrogate(140,seed=31);real=complete_search(x)
    a=null_search(x,replicates=2,seed=45);b=null_search(x,replicates=2,seed=45)
    assert a==b and len(a)==4
    assert all(r['rebuilt'] and r['space']==real['space'] for r in a)
    assert len({r['representation_hash'] for r in a})==4
    assert any(r['maxima']!=real['maxima'] for r in a)
    comparison=compare_maxima(real,a)
    assert len(comparison)==10
    for row in comparison:
        values=[r['maxima'][row['family']] for r in a if r['null_model']==row['null_model']]
        p=(1+sum(v>=real['maxima'][row['family']] for v in values))/3
        assert row['global_p']==p and row['adjusted_p']==min(1,5*p)


def test_future_source_and_empty_null_rejected():
    with pytest.raises(ValueError):complete_search(iid_surrogate(1246,seed=19))
    with pytest.raises(ValueError):null_search(iid_surrogate(140,seed=1),replicates=0)
    with pytest.raises(ValueError):compare_maxima({'maxima':dict.fromkeys(FAMILIES,0)},[])
