import numpy as np
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate


def test_complete_deterministic_surrogate_rebuild_and_scope_margins():
    from src.analysis.randomness_null import null_search
    from src.analysis.randomness_battery import scope_histories,track_view,metric_vector
    x=iid_surrogate(1245,seed=12)
    a=null_search(x,replicates=1,seed=260000);b=null_search(x,replicates=1,seed=260000)
    actual=scope_histories(x)
    for one,two in zip(a,b):
        for scope,entry in one['scopes'].items():
            np.testing.assert_array_equal(entry['raw_values'],two['scopes'][scope]['raw_values'])
            assert entry['rebuilt'] and entry['row_six']
            if one['track']=='fixed_margins':assert entry['margins_preserved']
            child=entry['seed'];n=len(actual[scope])
            null=iid_surrogate(n,seed=child) if one['track']=='iid' else constrained_surrogate(actual[scope],seed=child)
            raw=track_view(metric_vector(null),one['track'])
            np.testing.assert_array_equal(raw['values'],entry['raw_values'])
            assert entry['units']==(2200 if one['track']=='iid' else 2147)
