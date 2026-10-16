import numpy as np
import pytest


def test_causal_gap_and_never_seen():
    from src.analysis.gap3d import causal_states
    x=np.zeros((105,45),bool); x[99,16]=True; x[103,16]=True
    gap,mean,relative=causal_states(x)
    assert np.isnan(gap[99,16]) # prediction for draw100 cannot see its own appearance
    assert gap[100,16]==0 and gap[103,16]==3 and gap[104,16]==0
    assert mean[104,16]==4 and relative[104,16]==0
    assert np.isnan(mean[103,16]) and np.isnan(gap[:,0]).all()
    changed=x.copy(); changed[103,16]=False
    assert np.array_equal(causal_states(changed)[0][:104],gap[:104],equal_nan=True)


def test_gap_encoder_training_only_and_missing():
    from src.analysis.gap3d import GapEncoder,causal_states
    from src.analysis.spatiotemporal import iid_surrogate
    x=iid_surrogate(120,seed=3); g,m,r=causal_states(x)
    encoder=GapEncoder().fit(g[:100],r[:100],cutoff=100)
    before=encoder.configuration()
    z=encoder.transform(np.array([[np.nan,0,2,999]]),np.array([[np.nan,0,.5,99]]),'quantile')
    assert z[0,0]==-1 and z[0,-1]==2 and encoder.configuration()==before
    exact=encoder.transform(g,r,'clipped')
    assert exact.max()==encoder.cap and (exact[np.isnan(g)]==-1).all()
    assert encoder.transform(g,r,'relative')[np.isnan(r)].max()==-1
    with pytest.raises(ValueError): GapEncoder().fit(g,r,cutoff=100)


def test_sparse_state_table_alignment(history):
    from src.analysis.gap3d import state_table
    table=state_table(history,cutoff=12)
    assert len(table)==12*45 and (table.feature_cutoff==table.target_draw-1).all()
    assert table.groupby('target_draw').appeared_next.sum().eq(6).all()
    row=table.query('target_draw==3 and number==1').iloc[0]
    assert row.current_gap==1 and row.appeared_next==1
    assert table.query('number==45').appeared_next.eq(0).all()
    assert table.query('number==45').current_gap.isna().all()
    with pytest.raises(ValueError): state_table(history,cutoff=11)
