import itertools
import numpy as np
import pandas as pd
import pytest
from src.models.hazard import hazard_bucket, hazard_table, GapHazardModel
from src.models.bayesian import BayesianModel
from src.models.bernoulli_hmm import forward_filter, BernoulliHMM
from src.models.regime import HMMModel


def rows(n=140):
    rng=np.random.default_rng(3)
    result=[]
    gaps=np.zeros(45)
    for t in range(105,105+n):
        winners=rng.choice(45,6,replace=False)
        for j in range(45):
            result.append(dict(target_draw=t,feature_cutoff=t-1,number=j+1,
                current_gap=gaps[j],mean_gap=7.5,gap_std=7.,gap_ratio=gaps[j]/7.5,
                appeared_next=int(j in winners)))
        gaps+=1
        gaps[winners]=0
    return pd.DataFrame(result)


def test_hazard_buckets_smoothing():
    assert hazard_bucket(np.array([0,1,2,5,10,20,50]),'gap').tolist()==[0,1,1,3,4,6,7]
    table=hazard_table(rows(),min_count=100)
    assert {'observations','appearances','probability','ci_low','ci_high','adequate'}<=set(table)
    m=GapHazardModel().fit(rows().assign(current_gap=0),cutoff=244)
    assert np.all((m.probabilities>0)&(m.probabilities<1))
    assert m.probabilities[-1]==pytest.approx(6/45)  # empty extreme bucket


def test_bayesian_posterior_and_online_cutoff():
    data=rows()
    model=BayesianModel().fit(data[data.target_draw<244],cutoff=243)
    d=model.diagnostics().set_index('number')
    successes=data[(data.number==1)&(data.target_draw<244)].appeared_next.sum()
    assert d.loc[1,'alpha']==2+successes
    assert d.loc[1,'beta']==13+139-successes
    current=data[data.target_draw==244].drop(columns='appeared_next')
    scores=model.score_rows(current)
    assert scores[1]==pytest.approx((2+successes)/(15+139))
    with pytest.raises(ValueError): model.score_rows(data[data.target_draw==244])
    with pytest.raises(ValueError): BayesianModel().fit(data,cutoff=243)
    bad=current.assign(target_draw=1245,feature_cutoff=1244)
    with pytest.raises(ValueError): model.score_rows(bad)


def test_bayesian_recency_exact_weights():
    data=rows(5)
    m=BayesianModel(half_life=2).fit(data,cutoff=109)
    w=2.**(-np.arange(4,-1,-1)/2)
    y=data[data.number==1].appeared_next.to_numpy()
    assert m.diagnostics().iloc[0].alpha==pytest.approx(2+w@y)
    assert m.diagnostics().iloc[0].observations==pytest.approx(w.sum())


def test_forward_filter_matches_enumeration():
    x=np.array([1,0,1]); a=np.array([[.8,.2],[.3,.7]]); p=np.array([.1,.6]); pi=np.array([.4,.6])
    filtered,ll=forward_filter(x,a,p,pi)
    weights=np.zeros(2)
    for states in itertools.product(range(2),repeat=3):
        w=pi[states[0]]
        for t,s in enumerate(states):
            w*=p[s] if x[t] else 1-p[s]
            if t: w*=a[states[t-1],s]
        weights[states[-1]]+=w
    np.testing.assert_allclose(filtered[-1],weights/weights.sum())
    assert ll==pytest.approx(np.log(weights.sum()))
    prefix,_=forward_filter(x[:2],a,p,pi)
    np.testing.assert_allclose(filtered[:2],prefix)


def test_hmm_fit_deterministic_normalized_sparse():
    x=np.random.default_rng(3).binomial(1,.13,130)
    a=BernoulliHMM(states=3,max_iter=5,seed=4).fit(x)
    b=BernoulliHMM(states=3,max_iter=5,seed=4).fit(x)
    np.testing.assert_allclose(a.emissions,b.emissions)
    np.testing.assert_allclose(a.transitions.sum(axis=-1),1)
    assert np.all(np.diff(a.emissions,axis=-1)>=0)
    assert np.isfinite(a.filtered).all()
    assert 0<a.next_score()[0]<1
    assert len(a.initializations)==2
    with pytest.raises(ValueError): BernoulliHMM().fit(x[:20])
    sparse=BernoulliHMM(max_iter=3).fit(np.zeros(120))
    assert np.isfinite(sparse.next_score()).all()


def test_hmm_model_online_uses_only_observed_prefix():
    data=rows(133)
    m=HMMModel(max_iter=3).fit(data[data.target_draw<=235],cutoff=235)
    cur=data[data.target_draw==236].drop(columns='appeared_next')
    before=m.score_rows(cur)
    assert before==m.score_rows(cur)  # repeat scoring never double-updates
    after=data[data.target_draw==237].drop(columns='appeared_next')
    scores=m.score_rows(after)
    assert set(scores)==set(range(1,46))
    bad=after.assign(target_draw=239,feature_cutoff=238)
    with pytest.raises(ValueError): m.score_rows(bad)


@pytest.mark.parametrize('factory',[BayesianModel,lambda:BayesianModel(half_life=52),lambda:HMMModel(max_iter=3),GapHazardModel])
def test_models_prefix_invariance_and_reject_future_fit(factory):
    data=rows(133); training=data[data.target_draw<=235]
    a=factory().fit(training.copy(),cutoff=235)
    changed=data.copy(); changed.loc[changed.target_draw>=236,'appeared_next']=1
    b=factory().fit(changed[changed.target_draw<=235],cutoff=235)
    current=data[data.target_draw==236].drop(columns='appeared_next')
    assert a.score_rows(current)==b.score_rows(current)
    with pytest.raises(ValueError): factory().fit(data,cutoff=235)


def test_online_bayesian_update_matches_expanding_refit():
    data=rows(133); training=data[data.target_draw<=235]
    for half_life in (None,52):
        m=BayesianModel(half_life=half_life).fit(training,cutoff=235)
        m.score_rows(data[data.target_draw==236].drop(columns='appeared_next'))
        current=data[data.target_draw==237].drop(columns='appeared_next')
        online=m.score_rows(current)
        refit=BayesianModel(half_life=half_life).fit(data[data.target_draw<=236],cutoff=236).score_rows(current)
        np.testing.assert_allclose(list(online.values()),list(refit.values()))


def test_hmm_recovers_obvious_synthetic_regimes_and_batch_agrees():
    x=np.tile(np.r_[np.zeros(100),np.ones(60),np.zeros(40)],3)
    model=BernoulliHMM().fit(x)
    assert model.emissions[0,0]<.05 and model.emissions[0,1]>.8
    assert np.all(np.diag(model.transitions[0])>.9)
    filtered,ll=forward_filter(x,model.transitions[0],model.emissions[0])
    np.testing.assert_allclose(model.filtered[:,0],filtered)
    assert model.log_likelihood[0]==pytest.approx(ll)


def test_hmm_null_deterministic_and_corrected():
    from src.analysis.regime_research import null_diagnostics
    a,s=null_diagnostics(rows(),numbers=(7,),repeats=2,seed=2,max_iter=3)
    b,t=null_diagnostics(rows(),numbers=(7,),repeats=2,seed=2,max_iter=3)
    pd.testing.assert_frame_equal(a,b); pd.testing.assert_frame_equal(s,t)
    assert len(a)==6 and len(s)==6
    assert s.permutation_p.between(1/3,1).all()
    assert (s.p_bonferroni>=s.permutation_p).all()
