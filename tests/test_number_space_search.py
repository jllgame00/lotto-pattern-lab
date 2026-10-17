import numpy as np
import pandas as pd
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.analysis.number_space_search import complete_search,compare_nulls,spacing_reference


def test_planted_hot_zone_and_complete_search_parity():
    x=np.zeros((60,45),bool);x[:,20:26]=True
    reference=spacing_reference()
    a=complete_search(x,reference,details=True);b=complete_search(x,reference,details=False)
    assert a['maxima']==b['maxima'] and a['space']==b['space']
    r=a['range_leaders'].iloc[0]
    assert r.start_number<=21 and r.end_number>=26 and r.raw_z>10
    assert a['maxima']['persistence']==51
    assert set(a['maxima'])=={'range_density','neighborhood','persistence','movement','spacing_clustering','spacing_motif'}
    assert len(a['spacing'])==60


def test_both_seeded_surrogates_preserve_lotto_rows_and_recompute_search():
    x=iid_surrogate(60,seed=1);s=constrained_surrogate(x,seed=2)
    assert np.array_equal(s.sum(axis=0),x.sum(axis=0)) and np.all(s.sum(axis=1)==6)
    a,draws=compare_nulls(x,replicates=2,seed=4)
    b,again=compare_nulls(x,replicates=2,seed=4)
    pd.testing.assert_frame_equal(a,b);pd.testing.assert_frame_equal(draws,again)
    assert len(draws)==4 and draws.recomputed_features.all()
    assert set(draws.null_model)=={'iid','fixed_margins'}
    assert (a.adjusted_p==np.minimum(1,6*a.global_p)).all()
    assert (a.global_p>=1/3).all()
    for row in a.itertuples():
        null=draws[draws.null_model==row.null_model][row.statistic]
        assert row.global_p==(1+int((null>=row.real_max).sum()))/3
