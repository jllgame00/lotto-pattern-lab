import numpy as np
import pytest

def test_joint_mapping_and_missing_policy():
    from src.analysis.joint_state import combine_states
    g=np.repeat(np.arange(3),3);f=np.tile(np.arange(3),3)
    assert combine_states(g,f).tolist()==list(range(9))
    assert combine_states(np.array([-1,0,2]),np.array([2,-1,0])).tolist()==[-1,-1,6]

def test_joint_causal_timing_and_training_boundaries():
    from src.analysis.joint_state import JointEncoder
    from src.analysis.spatiotemporal import iid_surrogate
    x=iid_surrogate(140,seed=7);m=JointEncoder().fit(x[:110],cutoff=110)
    config=m.configuration();a=m.transform(x[:120]);changed=x[:120].copy();changed[119]=~changed[119]
    b=m.transform(changed)
    for key in a: assert np.array_equal(a[key][:120],b[key][:120],equal_nan=True)
    assert m.configuration()==config and (a['joint_state'][:26]==-1).all()
    assert np.isnan(a['gap'][0]).all()
    assert (a['frequency_count'][26]==x[:26].sum(axis=0)).all()
    with pytest.raises(ValueError): JointEncoder().fit(x,cutoff=110)

def test_joint_table_support_and_bonus(history):
    from test_features import extend
    from src.analysis.joint_state import state_table,support_audit
    data=extend(history,120);t=state_table(data,cutoff=120)
    assert len(t)==120*45 and (t.feature_cutoff==t.target_draw-1).all()
    assert t.groupby('target_draw').appeared_next.sum().eq(6).all()
    support=support_audit(t)
    assert support.joint_state.tolist()==list(range(9)) and support.observations.sum()==t.joint_state.ge(0).sum()
