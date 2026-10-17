"""Numerical contracts for constrained Lotto spectra; no actual future draws."""
import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def module():
    from src.analysis import random_matrix
    return random_matrix


def test_sample_correlation_covariance_and_structural_direction():
    x=iid_surrogate(208,seed=22)
    corr=module().fit_matrix(x)
    cov=module().fit_matrix(x,kind='covariance')
    np.testing.assert_allclose(corr['matrix'],np.corrcoef(x.astype(float),rowvar=False),atol=1e-14)
    np.testing.assert_allclose(cov['matrix'],np.cov(x.astype(float),rowvar=False),atol=1e-14)
    np.testing.assert_allclose(corr['matrix']@corr['std'],0,atol=1e-14)
    assert np.linalg.norm(corr['matrix']@np.ones(45))>.01
    np.testing.assert_allclose(cov['matrix']@np.ones(45),0,atol=1e-14)
    for fit in (corr,cov):
        assert fit['eigenvalues'].shape==(44,)
        assert np.all(np.diff(fit['eigenvalues'])<=0)
        np.testing.assert_allclose(fit['eigenvectors'].T@fit['eigenvectors'],np.eye(44),atol=1e-13)
        np.testing.assert_allclose(fit['matrix']@fit['eigenvectors'],fit['eigenvectors']*fit['eigenvalues'],atol=1e-13)
        np.testing.assert_allclose(fit['eigenvalues'].sum(),np.trace(fit['matrix']),atol=1e-13)
        assert fit['cumulative_variance'][-1]==pytest.approx(1)


@pytest.mark.parametrize('case',['future','wrong_width','wrong_sum','nonbinary','nan','cutoff','kind'])
def test_invalid_research_inputs(case):
    x=iid_surrogate(104,seed=1).astype(float);kwargs={}
    if case=='future':x=iid_surrogate(1246,seed=1)
    if case=='wrong_width':x=x[:,:44]
    if case=='wrong_sum':x[0]=0
    if case=='nonbinary':x[0,:2]=.5
    if case=='nan':x[0,0]=np.nan
    if case=='cutoff':kwargs['cutoff']=103
    if case=='kind':kwargs['kind']='arbitrary'
    with pytest.raises(ValueError):module().fit_matrix(x,**kwargs)


def test_inactive_columns_are_safe_and_not_false_nontrivial_modes():
    x=np.zeros((104,45),bool);x[:,:5]=True
    x[np.arange(104),5+np.arange(104)%40]=True
    fit=module().fit_matrix(x)
    assert fit['active'].sum()==40 and len(fit['eigenvalues'])==39
    assert not fit['eigenvectors'][:5].any()
    np.testing.assert_array_equal(fit['matrix'][:5],0)
    x[:]=False;x[:,:6]=True
    for kind in ('correlation','covariance'):
        constant=module().fit_matrix(x,kind=kind)
        assert not constant['matrix'].any()
        assert len(constant['eigenvalues'])==0
        assert constant['entropy']==constant['effective_rank']==0


def test_ipr_participation_entropy_and_effective_rank_hand_values():
    v=np.array([[1.,1/np.sqrt(2)],[0.,1/np.sqrt(2)],[0.,0.]])
    np.testing.assert_allclose(module().participation(v)['ipr'],[1.,.5])
    np.testing.assert_allclose(module().participation(v)['pr'],[1.,2.])
    summary=module().spectrum_summary(np.array([2.,2.,0.]))
    assert summary['entropy']==pytest.approx(np.log(2))
    assert summary['effective_rank']==pytest.approx(2)
    np.testing.assert_allclose(summary['cumulative_variance'],[.5,1.,1.])
    assert module().spectrum_summary(np.zeros(3))['effective_rank']==0


def test_planted_collective_binary_mode_is_stronger_than_iid():
    rng=np.random.default_rng(2201);x=np.zeros((624,45),bool)
    for i in range(len(x)):
        pool=np.arange(0,22) if i%2==0 else np.arange(22,45)
        x[i,rng.choice(pool,6,replace=False)]=True
    planted=module().fit_matrix(x)
    null=module().fit_matrix(iid_surrogate(624,seed=2201))
    assert planted['eigenvalues'][0]>5
    assert null['eigenvalues'][0]<2
    assert abs(planted['eigenvectors'][:,0]@np.r_[np.ones(22),-np.ones(23)]/np.sqrt(45))>.95
    assert null['structural_residual']<1e-12


def test_sign_and_near_degenerate_rotation_alignment():
    reference=np.eye(4)[:,:3]
    theta=.73;rotation=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
    candidate=reference.copy();candidate[:,:2]=reference[:,:2]@rotation;candidate[:,2]*=-1
    aligned=module().align_modes(reference,candidate,np.array([2.,1.99,1.]))
    np.testing.assert_allclose(aligned,reference,atol=1e-13)
    vectors=module().canonical_signs(-reference)
    np.testing.assert_array_equal(vectors,reference)


def test_principal_angles_and_projection_distance_ignore_sign_and_rotation():
    a=np.eye(4)[:,:2];b=a@np.array([[0.,-1.],[1.,0.]])
    same=module().subspace_comparison(a,b,2)
    assert same['overlap']==pytest.approx(1)
    assert same['projection_distance']==pytest.approx(0,abs=1e-7)
    np.testing.assert_allclose(same['principal_angles'],0,atol=3e-8)
    other=module().subspace_comparison(a,np.eye(4)[:,2:],2)
    assert other['overlap']==pytest.approx(0)
    assert other['projection_distance']==pytest.approx(2)
    np.testing.assert_allclose(other['principal_angles'],np.pi/2)


def test_rolling_grid_and_training_prefix_are_bounded():
    m=module()
    np.testing.assert_array_equal(m.rolling_endpoints(624,416),[416,520,624])
    np.testing.assert_array_equal(m.rolling_endpoints(900,624),[624,728,832,900])
    for n,w in ((1246,104),(103,104),(900,312)):
        with pytest.raises(ValueError):m.rolling_endpoints(n,w)
    x=iid_surrogate(624,seed=4)
    prefix=m.fit_matrix(x[:416],cutoff=416)
    x[416:]=iid_surrogate(208,seed=5)
    np.testing.assert_array_equal(prefix['matrix'],m.fit_matrix(x[:416])['matrix'])


@pytest.mark.parametrize('lag',[1,2,4,8,13])
def test_lagged_cross_correlation_uses_two_local_scalers_and_singular_values(lag):
    x=iid_surrogate(208,seed=13).astype(float)
    result=module().lagged_spectrum(x,lag)
    a=x[:-lag];b=x[lag:]
    za=(a-a.mean(0))/a.std(0,ddof=1);zb=(b-b.mean(0))/b.std(0,ddof=1)
    expected=za.T@zb/(len(a)-1)
    np.testing.assert_allclose(result['matrix'],expected,atol=1e-14)
    assert not np.allclose(expected,expected.T)
    np.testing.assert_allclose(result['singular_values'],np.linalg.svd(expected,compute_uv=False)[:44],atol=1e-13)
    np.testing.assert_allclose(expected@result['right_vectors'],result['left_vectors']*result['singular_values'],atol=1e-13)
    np.testing.assert_allclose(expected@result['right_std'],0,atol=1e-13)
    np.testing.assert_allclose(result['left_std']@expected,0,atol=1e-13)


@pytest.mark.parametrize('lag',[0,3,True,1.5,-1])
def test_undeclared_or_invalid_lags_are_rejected(lag):
    with pytest.raises(ValueError):module().lagged_spectrum(iid_surrogate(104,seed=3),lag)


def test_descriptive_mp_reference_uses_effective_dimension_only():
    mp=module().mp_reference(101,25,variance=1.)
    assert mp['aspect_ratio']==pytest.approx(.25)
    assert mp['lower']==pytest.approx(.25)
    assert mp['upper']==pytest.approx(2.25)
    assert mp['descriptive_only']
