import numpy as np
import pytest


def test_independent_maximum_audit_handles_absolute_entropy_and_tamper():
    from src.analysis.topology_audit import verify_maxima
    c=dict(mean=np.array([0.,0.,5.,0.]),std=np.ones(4),eligible=np.ones(4,bool),
           families=['h0_longest','h0_total','h0_entropy','h0_tail'])
    values=np.array([[1.,2.,3.,4.],[2.,3.,8.,5.]])
    expected=dict(h0_longest=np.array([1.,2.]),h0_total=np.array([2.,3.]),h0_entropy=np.array([2.,3.]),h0_tail=np.array([4.,5.]))
    verify_maxima(values,c,expected)
    with pytest.raises(AssertionError):verify_maxima(values,c,dict(expected,h0_entropy=np.array([-2.,3.])))


def test_independent_kruskal_preserves_zero_merges():
    from src.analysis.topology_audit import kruskal_deaths
    d=np.array([[0.,0.,1.],[0.,0.,1.],[1.,1.,0.]])
    np.testing.assert_array_equal(kruskal_deaths(d),[0.,1.])
