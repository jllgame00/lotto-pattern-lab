import numpy as np


def test_symbol_agreement_is_descriptive_and_detects_equivalent_encodings():
    from src.analysis.symbolic_diagnostics import agreement_matrix,transition_stability
    s=np.tile([0,1,0,1,1,0],60)
    enc=dict(a=dict(symbols=s,alphabet=2),b=dict(symbols=1-s,alphabet=2))
    names,m=agreement_matrix(enc)
    np.testing.assert_allclose(m,np.ones((2,2)))
    rows=transition_stability(s,2,0,1)
    assert rows and all(r['end']<=560 for r in rows)
    assert all(r['start']>=201 for r in rows)
