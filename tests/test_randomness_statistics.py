from math import comb
import numpy as np
import pytest


def matrix(draws):
    x=np.zeros((len(draws),45),bool)
    x[np.arange(len(draws))[:,None],np.array(draws)-1]=True
    return x


def test_exact_representations_and_six_constraint():
    from src.analysis.randomness_statistics import representations
    x=matrix([[1,2,3,4,5,6],[40,41,42,43,44,45]])
    r=representations(x)
    np.testing.assert_array_equal(r['numbers'],[[1,2,3,4,5,6],[40,41,42,43,44,45]])
    np.testing.assert_array_equal(r['gaps'],np.ones((2,5)))
    np.testing.assert_array_equal(r['shape'][:,0],[21,255])
    np.testing.assert_array_equal(r['bands'],[[6,0,0,0,0],[0,0,0,0,6]])
    x[0,9]=True
    with pytest.raises(ValueError):representations(x)


def test_transition_word_counts_and_lag_alignment():
    from src.analysis.randomness_statistics import transition_g,binary_word_counts,lag_correlation
    s=np.array([0,1,0,1,0,1])
    np.testing.assert_array_equal(binary_word_counts(s,2),[0,3,2,0])
    assert transition_g(s)>0
    assert lag_correlation(s,1)==pytest.approx(-1)
    assert lag_correlation(s,2)==pytest.approx(1)


def test_runs_gaps_and_censored_boundaries():
    from src.analysis.randomness_statistics import run_lengths,number_gap_statistics
    s=np.array([0,0,1,1,0,0,0,1,0,0])
    values,lengths=run_lengths(s)
    np.testing.assert_array_equal(values,[0,1,0,1,0])
    np.testing.assert_array_equal(lengths,[2,2,3,1,2])
    r=number_gap_statistics(s)
    assert r['absence']==3 and r['appearance']==2 and r['runs']==5
    np.testing.assert_array_equal(r['gaps'],[1,4])


def test_overlap_distribution_matches_hypergeometric_and_real_pairs():
    from src.analysis.randomness_statistics import overlap_probabilities,overlap_statistics
    p=overlap_probabilities()
    assert p.sum()==pytest.approx(1)
    assert p[0]==pytest.approx(comb(39,6)/comb(45,6))
    assert np.dot(np.arange(7),p)==pytest.approx(.8)
    x=matrix([[1,2,3,4,5,6],[1,2,3,4,5,7],[8,9,10,11,12,13]])
    r=overlap_statistics(x,1)
    np.testing.assert_array_equal(r['overlaps'],[5,0])
    assert r['jaccard']==pytest.approx((5/7)/2)


def test_pair_triple_counting_and_opportunity_corrected_differences():
    from src.analysis.randomness_statistics import pair_triple_counts,difference_probabilities,adjacent_gap_probabilities
    x=matrix([[1,2,3,4,5,6],[1,2,3,7,8,9]])
    pairs,pc,triples,tc=pair_triple_counts(x)
    assert pc[np.flatnonzero((pairs==[0,1]).all(1))[0]]==2
    assert tc[np.flatnonzero((triples==[0,1,2]).all(1))[0]]==2
    assert pc.sum()==30 and tc.sum()==40
    p=difference_probabilities();assert p.sum()==pytest.approx(1)
    assert p[0]/p[-1]==44
    a=adjacent_gap_probabilities();assert a.sum()==pytest.approx(1)
    assert a[0]==pytest.approx(comb(44,5)/comb(45,6))


def test_entropy_and_spectral_are_finite_for_constant_and_alternating_data():
    from src.analysis.randomness_statistics import entropy_deficit,spectral_statistics
    s=np.tile([0,1],100)
    assert .99<entropy_deficit(s,2)<1.01  # 2bits independent minus1bit alternating blocks.
    assert entropy_deficit(np.zeros(200,int),4)==0
    assert all(np.isfinite(v) for v in spectral_statistics(s))
