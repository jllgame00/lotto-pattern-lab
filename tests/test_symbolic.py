import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def test_all_encodings_and_development_boundaries_are_causal():
    from src.analysis.symbolic import encode_all
    x=iid_surrogate(350,seed=8);other=x.copy();other[230:]=iid_surrogate(120,seed=55)
    one=encode_all(x);two=encode_all(other)
    assert {k:v['alphabet'] for k,v in one.items()}==dict(parity=7,balance=13,sum3=3,sum4=4,range3=3,range4=4,spacing=6,band=10)
    for k in one:
        assert one[k]['boundaries']==two[k]['boundaries']
        np.testing.assert_array_equal(one[k]['symbols'][:30],two[k]['symbols'][:30])
        assert one[k]['first_draw']==201 and len(one[k]['symbols'])==150


def test_deterministic_symbol_known_draw_and_full_alphabet_support():
    from src.analysis.symbolic import deterministic_symbols,support_audit
    a=np.array([[1,2,3,23,44,45],[2,4,6,8,10,12]])
    r=deterministic_symbols(a)
    np.testing.assert_array_equal(r['parity'],[4,0])
    np.testing.assert_array_equal(r['balance'],[10,6])
    np.testing.assert_array_equal(r['band'],[1,1])
    s=support_audit(np.array([0,0,0,1]),3)
    assert s['counts']==[3,1,0] and s['minimum_support']==0 and s['observed_symbols']==2
    assert s['rare_symbols']==[0,1,2]


def test_order0_order1_smoothing_and_context_alignment():
    from src.analysis.symbolic import transition_probabilities,prequential_losses
    s=np.array([0,1,0,1,0,1])
    p=transition_probabilities(s,2,1,1)
    np.testing.assert_allclose(p,[[.2,.8],[.75,.25]])
    losses=prequential_losses(s,2,min_support=1)
    # Target index4=0, previous context1 had one prior successor0.
    assert np.exp(-losses[4,1,1])==pytest.approx(2/3)
    assert np.isfinite(losses).all()


def test_order2_order3_and_future_append_do_not_change_past_probabilities():
    from src.analysis.symbolic import prequential_losses
    rng=np.random.default_rng(32);s=rng.integers(0,3,100)
    a=prequential_losses(s,3,min_support=1)
    b=prequential_losses(np.r_[s[:60],rng.integers(0,3,40)],3,min_support=1)
    np.testing.assert_array_equal(a[:60],b[:60])
    assert a.shape==(100,4,2)


def test_conditional_entropy_words_forbidden_runs_and_lags():
    from src.analysis.symbolic import conditional_entropy,word_diagnostic,run_diagnostic,symbolic_lag
    s=np.tile([0,1],100)
    assert conditional_entropy(s,2,0)==pytest.approx(1)
    assert conditional_entropy(s,2,1)==0
    r=word_diagnostic(s,2,2)
    np.testing.assert_array_equal(r['counts'],[0,100,99,0])
    assert r['missing_max_expected']>40
    runs=run_diagnostic(s,2)
    assert runs['longest']==1 and runs['lengths'].tolist()==[1]*200
    assert symbolic_lag(s,2,2)==pytest.approx(.5)


def test_synthetic_order1_and_order2_recovery_and_iid_rejection():
    from src.analysis.symbolic import select_order
    rng=np.random.default_rng(19)
    s=np.zeros(4000,dtype=int)
    for t in range(1,len(s)):s[t]=s[t-1]^(rng.random()<.08)
    assert select_order(s,2,2600)['order']==1
    s=np.zeros(6000,dtype=int);s[1]=1
    for t in range(2,len(s)):s[t]=s[t-1]^s[t-2]^(rng.random()<.04)
    assert select_order(s,2,4000)['order']==2
    iid=rng.integers(0,3,6000)
    assert select_order(iid,3,4000)['order']==0


def test_word_support_does_not_count_terminal_prefix_without_successor():
    from src.analysis.symbolic import word_diagnostic
    s=np.r_[np.ones(9,int),np.zeros(30,int),1]
    r=word_diagnostic(s,2,2)
    assert r['expected'][2]>=5
    assert not r['supported'][2]  # Only9 usable outgoing prefixes1, not10.


def test_hand_calculated_order2_order3_and_order0_heldout_loss():
    from src.analysis.symbolic import prequential_losses
    s=np.array([0,0,1,0,0,1,0,0,1])
    losses=prequential_losses(s,2,min_support=1)
    assert np.exp(-losses[8,0,1])==pytest.approx(.3)
    assert np.exp(-losses[8,1,1])==pytest.approx(3/7)
    assert np.exp(-losses[8,2,1])==pytest.approx(.75)
    assert np.exp(-losses[8,3,1])==pytest.approx(2/3)


def test_complete_word_enumeration_and_dense_bic_penalty():
    from src.analysis.symbolic import all_words,bic
    np.testing.assert_array_equal(all_words(2,3),[[0,0,0],[0,0,1],[0,1,0],[0,1,1],[1,0,0],[1,0,1],[1,1,0],[1,1,1]])
    s=np.tile([0,1],500)
    assert bic(s,2,1)==pytest.approx(2*np.log(999))
    assert bic(s,2,3)==pytest.approx(8*np.log(997))
    assert bic(s,2,0)==pytest.approx(2000*np.log(2)+np.log(1000))


def test_unseen_context_backoff_equals_positive_order0_with_small_support():
    from src.analysis.symbolic import prequential_losses
    s=np.array([0,1,2,2,1,0,2,0])
    loss=prequential_losses(s,3)
    for k in (1,2,3):np.testing.assert_array_equal(loss[:,k],loss[:,0])
    assert np.all((np.exp(-loss)>0)&(np.exp(-loss)<1))
