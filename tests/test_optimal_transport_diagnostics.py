import numpy as np
import pytest


def test_descriptive_summary_preserves_causal_barycenter_targets():
    from src.analysis.optimal_transport_diagnostics import descriptive_summary
    from src.analysis.spatiotemporal import iid_surrogate
    summary=descriptive_summary(iid_surrogate(156,seed=73))
    assert summary['draws']==156
    assert summary['consecutive_W1']['count']==155
    assert summary['barycenter']['26_W1']['first_target']==27
    assert summary['barycenter']['26_W1']['sorted_mean_max_difference']==0
    assert summary['geodesic']['descriptive_only'] is True
    assert len(summary['lags'])==7
