import numpy as np
import pytest

@pytest.mark.parametrize('window',[10,26,52])
def test_frequency_exact_past_window_and_relative(window):
    from src.analysis.frequency3d import frequency_states
    x=np.zeros((90,45),bool); x[0,0]=True; x[window-1,0]=True; x[window,0]=True
    f=frequency_states(x,window)
    assert np.isnan(f['count'][:window]).all()
    assert f['count'][window,0]==2 and f['rate'][window,0]==2/window
    assert f['count'][window+1,0]==2 and f['prior_rate'][window+1,0]==3/(window+1)
    assert f['relative'][window+1,0]==pytest.approx((2/window)/(3/(window+1)))
    assert np.isnan(f['relative'][:,1]).all()
    changed=x.copy();changed[window:]=True
    for key,value in f.items(): assert np.array_equal(frequency_states(changed,window)[key][:window+1],value[:window+1],equal_nan=True)

def test_encoder_training_only_and_equivalent_count_rate():
    from src.analysis.frequency3d import frequency_states,FrequencyEncoder
    from src.analysis.spatiotemporal import iid_surrogate
    f=frequency_states(iid_surrogate(130,seed=8),26)
    enc=FrequencyEncoder(26).fit({k:v[:100] for k,v in f.items()},cutoff=100)
    before=enc.configuration()
    assert np.array_equal(enc.transform(f,'count'),enc.transform(f,'rate'))
    enc.transform(f);assert enc.configuration()==before
    assert (enc.transform(f)[:26]==-1).all()
    with pytest.raises(ValueError): FrequencyEncoder(26).fit(f,cutoff=100)

def test_frequency_table_main_only(history):
    from test_features import extend
    from src.analysis.frequency3d import frequency_table
    data=extend(history,110); t=frequency_table(data,cutoff=110)
    assert len(t)==110*45*3 and (t.feature_cutoff==t.target_draw-1).all()
    assert t.groupby(['window','target_draw']).appeared_next.sum().eq(6).all()
