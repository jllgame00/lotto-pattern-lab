"""Known finite metric-space H0 and frozen Lotto cloud contracts."""
import numpy as np
import pytest
from scipy.spatial.distance import pdist,squareform
from scipy.sparse.csgraph import minimum_spanning_tree
from src.analysis.spatiotemporal import iid_surrogate


def module():
    from src.analysis import topology
    return topology


def test_five_cloud_configurations_and_hand_checked_set_distances():
    configs=module().configurations()
    assert [c.key for c in configs]==['A_jaccard','A_hamming','B_euclidean','C26_euclidean','C52_euclidean']
    x=np.zeros((2,45),bool);x[0,:6]=True;x[1,4:10]=True
    assert module().build_cloud(x,configs[0])['distances'][0,1]==pytest.approx(.8)
    assert module().build_cloud(x,configs[1])['distances'][0,1]==pytest.approx(8/45)


def test_shape_frozen_coordinates_local_scaling_and_constants():
    m=module();x=iid_surrogate(208,seed=23)
    cloud=m.build_cloud(x,m.configurations()[2],start=1,end=104)
    changed=x.copy();changed[104:]=iid_surrogate(104,seed=24)
    again=m.build_cloud(changed,m.configurations()[2],start=1,end=104)
    np.testing.assert_array_equal(cloud['values'],again['values'])
    np.testing.assert_array_equal(cloud['mean'],again['mean'])
    np.testing.assert_allclose(cloud['values'].mean(0),0,atol=1e-13)
    np.testing.assert_allclose(cloud['values'].std(0),1,atol=1e-13)
    constant=np.zeros((104,45),bool);constant[:,np.array([1,2,3,10,20,45])-1]=True
    c=m.build_cloud(constant,m.configurations()[2])
    np.testing.assert_allclose(c['mean'],[81,44,np.sqrt(2891/12),8.8,np.sqrt(77.76),2,3])
    assert not c['values'].any() and not c['distances'].any()


@pytest.mark.parametrize('n,w,points,first_start',[(1245,26,47,24),(1245,52,23,50),(208,26,8,1),(208,52,4,1)])
def test_activity_clouds_use_disjoint_end_aligned_blocks(n,w,points,first_start):
    m=module();config=next(c for c in m.configurations() if c.window==w)
    x=iid_surrogate(n,seed=26);c=m.build_cloud(x,config)
    assert c['point_count']==points and c['block_starts'][0]==first_start and c['point_draws'][-1]==n
    assert np.all(c['block_starts'][1:]>c['point_draws'][:-1])
    np.testing.assert_allclose(c['values'].sum(1),6)
    for i,(a,b) in enumerate(zip(c['block_starts'],c['point_draws'])):
        np.testing.assert_array_equal(c['values'][i],x[a-1:b].mean(0))


def test_h0_known_two_clusters_excludes_one_infinite_bar():
    d=squareform(pdist(np.array([0.,1.,9.,10.])[:,None]))
    result=module().h0_persistence(d)
    np.testing.assert_array_equal(result['finite_intervals'],[[0,1],[0,1],[0,8]])
    assert result['infinite_components']==1 and np.isinf(result['infinite_interval'][1])
    assert result['longest']==8 and result['total']==10
    assert result['entropy']==pytest.approx(-.2*np.log(.1)-.8*np.log(.8))
    assert result['tail']==pytest.approx(.8)


def test_h0_matches_independent_scipy_mst_on_positive_distances():
    d=squareform(pdist(np.random.default_rng(23).normal(size=(20,3))))
    expected=np.sort(minimum_spanning_tree(d).data)
    np.testing.assert_allclose(module().h0_persistence(d)['finite_intervals'][:,1],expected)


def test_duplicates_zero_edges_ties_and_single_component_are_preserved():
    m=module();d=np.array([[0.,0.,1.],[0.,0.,1.],[1.,1.,0.]])
    r=m.h0_persistence(d)
    np.testing.assert_array_equal(r['finite_intervals'][:,1],[0,1])
    np.testing.assert_array_equal(r['edges'],m.h0_persistence(d)['edges'])
    zero=m.h0_persistence(np.zeros((4,4)))
    assert len(zero['finite_intervals'])==3 and zero['total']==zero['entropy']==zero['tail']==0
    single=m.h0_persistence(np.zeros((1,1)))
    assert len(single['finite_intervals'])==0 and single['infinite_components']==1


def test_distance_concentration_has_hand_checked_scale_and_zero_guard():
    d=squareform(pdist(np.array([0.,1.,9.,10.])[:,None]))
    r=module().distance_diagnostics(d)
    assert r['median_pairwise']==8.5 and r['median_nearest']==1
    assert r['variance']==pytest.approx(131/9)
    assert r['nearest_median_ratio']==pytest.approx(2/17)
    constant=module().distance_diagnostics(np.zeros((3,3)))
    assert constant['degenerate'] and np.isnan(constant['nearest_median_ratio'])


@pytest.mark.parametrize('d',[np.ones((2,3)),np.array([[0.,-1],[-1,0]]),np.array([[0.,1],[2,0]]),np.eye(2),np.array([[0.,np.nan],[np.nan,0.]])])
def test_invalid_metric_matrices_rejected(d):
    for function in (module().h0_persistence,module().distance_diagnostics):
        with pytest.raises(ValueError):function(d)


@pytest.mark.parametrize('case',['future','wrong_width','wrong_sum','nonbinary','cutoff','future_end','bool_start'])
def test_research_cloud_boundaries_reject_before_slicing(case):
    x=iid_surrogate(104,seed=6).astype(float);kwargs={}
    if case=='future':x=iid_surrogate(1246,seed=6);kwargs['end']=104
    if case=='wrong_width':x=x[:,:44]
    if case=='wrong_sum':x[0]=0
    if case=='nonbinary':x[0,:2]=.5
    if case=='cutoff':kwargs['cutoff']=103
    if case=='future_end':kwargs['end']=105
    if case=='bool_start':kwargs['start']=True
    with pytest.raises(ValueError):module().build_cloud(x,module().configurations()[0],**kwargs)


def test_rolling_grid_keeps_full_windows_and_exact_cutoff():
    m=module()
    np.testing.assert_array_equal(m.rolling_endpoints(900,624),[624,728,832,900])
    for n,w in ((1246,208),(207,208),(900,104)):
        with pytest.raises(ValueError):m.rolling_endpoints(n,w)
