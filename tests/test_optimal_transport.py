import numpy as np
import pytest
from scipy.stats import wasserstein_distance


def test_empirical_measure_and_exact_monotone_matching():
    from src.analysis.optimal_transport import empirical_measure, monotone_matching, wasserstein
    a=[6,1,5,2,4,3]; b=[2,4,6,8,10,12]
    positions,mass=empirical_measure(a)
    np.testing.assert_array_equal(positions,[1,2,3,4,5,6])
    np.testing.assert_allclose(mass,np.full(6,1/6))
    np.testing.assert_array_equal(monotone_matching(a,b),np.column_stack((np.arange(1,7),b)))
    assert wasserstein(a,b,1)==3.5
    assert wasserstein(a,b,2)==pytest.approx(np.sqrt(91/6))
    assert wasserstein(a,b,1)==pytest.approx(wasserstein_distance(a,b))
    with pytest.raises(ValueError): empirical_measure([1,1,2,3,4,5])


def test_transport_displacement_and_center_of_mass():
    from src.analysis.optimal_transport import transport_vector, displacement_summary
    d=transport_vector([1,3,5,7,9,11],[2,3,4,8,10,11])
    np.testing.assert_array_equal(d,[1,0,-1,1,1,0])
    s=displacement_summary(d)
    assert s['signed']==pytest.approx(1/3)
    assert s['absolute']==pytest.approx(2/3)
    assert s['rms']==pytest.approx(np.sqrt(2/3))
    assert s['variance']==pytest.approx(5/9)
    assert s['positive']==.5 and s['negative']==pytest.approx(1/6)
    assert s['center_of_mass_change']==s['signed']


def test_lag_alignment_direction_and_synthetic_processes():
    from src.analysis.optimal_transport import lag_distances, direction, acceleration
    base=np.array([1,5,9,13,17,21]); persistent=base+np.arange(6)[:,None]
    np.testing.assert_array_equal(lag_distances(persistent,2,1),np.full(4,2.))
    d=np.diff(persistent,axis=0)
    assert direction(d[:-1],d[1:])['cosine'].mean()==1
    np.testing.assert_array_equal(acceleration(d),np.zeros((4,6)))
    alternating=np.array([base+(i%2)*3 for i in range(8)])
    d=np.diff(alternating,axis=0)
    assert direction(d[:-1],d[1:])['cosine'].mean()==-1
    assert direction(d[:-1],d[1:])['coordinate_sign'].mean()==0


def test_vector_similarity_successor_and_no_shared_draws():
    from src.analysis.optimal_transport import vector_distances, successor_diagnostic
    d=np.array([[1]*6,[2]*6,[-1]*6,[-2]*6,[1]*6,[3]*6,[-1]*6,[-4]*6],float)
    assert vector_distances(d[:1],d[4:5],'cosine')[0,0]==pytest.approx(0)
    assert vector_distances(d[:1],d[2:3],'cosine')[0,0]==pytest.approx(2)
    r=successor_diagnostic(d,'euclidean')
    assert np.all(r['neighbor_indices']<=r['query_indices']-3)
    np.testing.assert_array_equal(r['query_next'],d[r['query_indices']+1])
    np.testing.assert_array_equal(r['neighbor_next'],d[r['neighbor_indices']+1])


def test_rolling_mass_overlap_and_exact_discrete_w1():
    from src.analysis.optimal_transport import rolling_distribution, discrete_w1, rolling_drift
    draws=np.array([[1,2,3,4,5,6],[2,3,4,5,6,7],[3,4,5,6,7,8]])
    p,ends=rolling_distribution(draws,2)
    np.testing.assert_array_equal(ends,[2,3]); np.testing.assert_allclose(p.sum(1),1)
    assert p[0,0]==pytest.approx(1/12) and p[0,1]==pytest.approx(2/12)
    assert discrete_w1(p[0],p[1])==pytest.approx(1)
    np.testing.assert_allclose(rolling_drift(draws,2,1)['distance'],[1])
    a=np.eye(45)[0];b=np.eye(45)[44]
    assert discrete_w1(a,b)==44
    with pytest.raises(ValueError): discrete_w1(a*2,b)


def test_barycenter_float_geodesic_and_mean_equivalence():
    from src.analysis.optimal_transport import barycenter, geodesic_residual, barycenter_diagnostic
    a=np.arange(1,7);b=a+3;c=a+6
    np.testing.assert_allclose(barycenter(np.array([a,b])),a+1.5)
    np.testing.assert_array_equal(geodesic_residual(np.array([a,b,c]),1),[0.])
    r=barycenter_diagnostic(np.array([a,b,c,c+1]),2,1)
    np.testing.assert_allclose(r['barycenters'],np.array([a+1.5,a+4.5]))
    np.testing.assert_allclose(r['next_distance'],[4.5,2.5])
    np.testing.assert_array_equal(r['barycenters'],r['sorted_mean_baseline'])


def test_discrete_w1_matches_independent_scipy_weighted_transport():
    from src.analysis.optimal_transport import discrete_w1
    rng=np.random.default_rng(6);axis=np.arange(1,46)
    for _ in range(8):
        a=rng.dirichlet(np.ones(45));b=rng.dirichlet(np.ones(45))
        assert discrete_w1(a,b)==pytest.approx(wasserstein_distance(axis,axis,a,b),abs=1e-12)


def test_successor_pair_statistics_are_independently_aligned():
    from src.analysis.optimal_transport import successor_diagnostic
    d=np.array([[i+1,2*i-3,3-i,1-i,2,4] for i in range(12)],float)
    r=successor_diagnostic(d,'euclidean')
    # Disjoint events0,3,6,9, each with successor1,4,7,10.
    np.testing.assert_array_equal(r['pair_events'],[0,3,6,9])
    expected=np.sqrt(np.mean((d[1]-d[4])**2))
    assert r['pair_next_distance'][0]==pytest.approx(expected)
    # First query3 can only retrieve event0, whose successor is event1.
    assert r['neighbor_indices'][0]==0
    assert r['nearest_next_distance'][0]==pytest.approx(np.sqrt(np.mean((d[4]-d[1])**2)))


def test_causal_barycenter_does_not_change_when_next_draw_is_changed():
    from src.analysis.optimal_transport import barycenter_diagnostic
    a=np.array([np.arange(1,7)+i for i in range(8)])
    b=a.copy();b[5:]=np.arange(35,41)
    first=barycenter_diagnostic(a,3);changed=barycenter_diagnostic(b,3)
    np.testing.assert_array_equal(first['barycenters'][:3],changed['barycenters'][:3])
    assert first['next_distance'][2]!=changed['next_distance'][2]


def test_w1_barycenter_is_median_and_geodesic_is_half_acceleration():
    from src.analysis.optimal_transport import barycenter, geodesic_residual, acceleration
    a=np.arange(1,7);draws=np.array([a,a+1,a+9])
    np.testing.assert_array_equal(barycenter(draws,p=1),a+1)
    np.testing.assert_allclose(geodesic_residual(draws,1),abs(acceleration(np.diff(draws,axis=0))).mean(1)/2)


def test_zero_transport_has_neutral_successor_gain():
    from src.analysis.optimal_transport import successor_diagnostic
    for metric in ('euclidean','cosine'):
        r=successor_diagnostic(np.zeros((12,6)),metric)
        np.testing.assert_array_equal(r['cosine_gain'],np.zeros(8))
        np.testing.assert_array_equal(r['distance_gain'],np.zeros(8))
