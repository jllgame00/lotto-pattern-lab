import numpy as np
import pytest


def test_independent_maxima_audit_rejects_tampered_saved_evidence():
    from src.analysis.random_matrix_audit import verify_maxima
    families=['largest','largest','smallest','localization','concentration','stability','lagged_secondary']
    values=np.array([[1.,6.,-1.,2.,3.,4.,5.],[7.,2.,-2.,4.,6.,8.,10.]])
    c=dict(mean=np.zeros(7),std=np.array([1.,2.,1.,1.,1.,1.,1.]),eligible=np.ones(7,bool),families=families)
    expected=dict(largest=np.array([3.,7.]),smallest=np.array([-1.,-2.]),localization=np.array([2.,4.]),
                  concentration=np.array([3.,6.]),stability=np.array([4.,8.]),lagged_secondary=np.array([5.,10.]))
    verify_maxima(values,c,expected)
    changed=dict(expected,largest=np.array([3.,6.]))
    with pytest.raises(AssertionError):verify_maxima(values,c,changed)


def test_audit_refuses_an_existing_result_before_loading_inputs(tmp_path):
    from src.analysis.random_matrix_audit import audit
    from src.analysis.spatiotemporal import iid_surrogate
    result=tmp_path/'audit_result.json';result.write_text('existing audit')
    with pytest.raises(FileExistsError):audit(iid_surrogate(1245,seed=22),tmp_path)
    assert result.read_text()=='existing audit'
