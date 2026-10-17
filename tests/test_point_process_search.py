import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def test_search_space_and_direction_inventory():
    from src.analysis.point_process_search import metric_vector,FAMILIES
    raw=metric_vector(iid_surrogate(520,seed=2020))
    assert len(raw['keys'])==len(set(raw['keys']))==36135
    assert raw['space']['family_cells']==dict(renewal=1710,self_positive=315,self_negative=315,
        cross_positive=13860,cross_negative=13860,kernel=6075)
    assert set(raw['families'])==set(FAMILIES)
    assert raw['space']['ordered_cross_pairs']==1980
    assert raw['space']['lags']==[1,2,3,4,8,13,26]


@pytest.fixture(scope='module')
def calibration():
    from src.analysis.point_process_search import fit_calibration
    return fit_calibration(520,replicates=4,seed=200999)


def test_own_global_max_and_cutoff_identity(calibration):
    from src.analysis.point_process_search import metric_vector,standardize,complete_search,FAMILIES
    raw=metric_vector(iid_surrogate(520,seed=2021));z=standardize(raw,calibration);found=complete_search(raw,calibration)
    for family in FAMILIES:
        assert found['maxima'][family]==pytest.approx(np.nanmax(z[np.array(raw['families'])==family]))
    with pytest.raises(ValueError):standardize(raw,dict(calibration,draws=900))
    with pytest.raises(ValueError):standardize(dict(raw,keys=raw['keys'][::-1]),calibration)


def test_surrogate_complete_rebuild_determinism_and_correction(calibration):
    from src.analysis.point_process_search import null_search,complete_search,metric_vector,compare_maxima
    x=iid_surrogate(520,seed=2022)
    a=null_search(x,{520:calibration},replicates=1,include_development=False)
    b=null_search(x,{520:calibration},replicates=1,include_development=False)
    real=complete_search(metric_vector(x),calibration)
    for left,right in zip(a,b):
        assert left['rebuilt'] and left['full']['space']==real['space']
        assert left['full']['representation_hash']!=real['representation_hash']
        np.testing.assert_equal(left['full']['raw_values'],right['full']['raw_values'])
    table=compare_maxima(real,a,scope='full')
    assert len(table)==12
    assert all(row['global_p']>=.5 and row['adjusted_p']==min(1,6*row['global_p']) for row in table)


def test_forbidden_draw_and_unsupported_scores():
    from src.analysis.point_process_search import metric_vector
    with pytest.raises(ValueError):metric_vector(np.ones((1246,45)))
    x=np.zeros((520,45),bool);x[:,:6]=True
    r=metric_vector(x)
    assert np.isnan(r['values']).any()
    assert all(np.isfinite(v) for v in r['values'][np.isfinite(r['values'])])
