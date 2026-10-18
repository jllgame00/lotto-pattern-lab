import numpy as np
import pytest


def test_leave_self_out_excludes_scored_history_and_conservative_ranks():
    from src.analysis.randomness_omnibus import leave_self_out
    a=np.array([[0.,0.],[0.,0.],[0.,0.],[0.,0.],[100.,-100.]])
    r=leave_self_out(a,['upper','lower'])
    np.testing.assert_array_equal(r['z'][-1],[100.,100.])
    np.testing.assert_array_equal(r['p'][-1],[.2,.2])
    np.testing.assert_array_equal(r['p'][0],[1.,1.])
    assert r['center'][-1,0]==0 and r['scale'][-1,0]==1


def test_two_sided_normalization_and_empirical_ties():
    from src.analysis.randomness_omnibus import leave_self_out
    a=np.array([[1.],[2.],[3.],[4.],[5.]])
    r=leave_self_out(a,['two_sided'])
    assert r['p'][0,0]==pytest.approx(.4) and r['p'][2,0]==1
    assert r['z'][0,0]==pytest.approx(r['z'][-1,0])


def test_entire_normalization_and_meta_pipeline_is_row_permutation_equivariant():
    from src.analysis.randomness_omnibus import leave_self_out,meta_scores
    a=np.random.default_rng(4).normal(size=(13,18));orient=['upper','lower','two_sided']*6;families=['a']*6+['b']*12
    r=leave_self_out(a,orient);m=meta_scores(r['z'],r['p'],families)
    permutation=np.random.default_rng(8).permutation(13)
    other=leave_self_out(a[permutation],orient);score=meta_scores(other['z'],other['p'],families)
    for k in ('z','p','center','scale'):np.testing.assert_allclose(other[k],r[k][permutation],rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(score['scores'],m['scores'][permutation],rtol=1e-12,atol=1e-12)


def test_sum_is_bounded_and_equal_family_weighted():
    from src.analysis.randomness_omnibus import sum_anomalies,family_weights
    z=np.array([9.,2.,2.,2.]);families=['small','large','large','large']
    assert sum_anomalies(z,families)==pytest.approx(2.5)  # .5*4 + .5*1
    weights=family_weights(families)
    assert weights[0]==pytest.approx(.5) and weights[1:].sum()==pytest.approx(.5)


def test_higher_criticism_detects_diffuse_alternative_and_handles_null_grid():
    from src.analysis.randomness_omnibus import higher_criticism
    null=(np.arange(200)+.5)/200
    weak=np.r_[np.full(60,.02),(np.arange(140)+.5)/140]
    a=higher_criticism(null);b=higher_criticism(weak)
    assert a['score']<1.5 and b['score']>10
    assert b['threshold']<=.5
    assert higher_criticism(np.ones(100))['score']==0


def test_omnibus_correction_and_leave_one_family_out_are_recalibrated():
    from src.analysis.randomness_omnibus import meta_scores,compare_scores,leave_one_family_out
    z=np.array([[8.,0.],[1.,0.],[2.,0.],[3.,0.],[4.,0.]])
    p=np.array([[.2,1],[1,1],[.8,1],[.6,1],[.4,1]])
    m=meta_scores(z,p,['a','b']);rows=compare_scores(m['scores'])
    assert rows[0]['global_p']==.2 and rows[0]['track_adjusted_p']==pytest.approx(.6)
    assert rows[0]['overall_adjusted_p']==1
    leave=leave_one_family_out(z,p,['a','b'])
    removed=leave['a']
    assert all(r['global_p']==1 for r in removed['comparison'])
