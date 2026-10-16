import numpy as np
import pytest


def api():
    from src.analysis import spatiotemporal
    return spatiotemporal


def test_matrix_main_only_and_cutoff(history):
    s=api(); x=s.lotto_matrix(history,cutoff=12)
    assert x.shape==(12,45) and np.all(x.sum(axis=1)==6)
    assert not x[:,44].any()
    with pytest.raises(ValueError): s.lotto_matrix(history,cutoff=11)
    with pytest.raises(ValueError): s.lotto_matrix(history.iloc[::-1],cutoff=12)


def test_shift_matches_and_boundaries():
    s=api(); x=np.zeros((8,45),bool)
    x[0,0]=x[2,3]=x[4,6]=x[6,9]=True
    x[0,44]=True # cannot translate +3; excluded from opportunity count
    row=s.shift_scores(x,max_dt=2,max_dn=3).query('delta_draw==2 and delta_number==3').iloc[0]
    assert row.observed_matches==3 and row.valid_opportunities==3
    assert row.overlap_area==6*42 and row.match_rate==1
    assert row.expected_rate==pytest.approx(6/45)
    assert row.lift==pytest.approx(7.5)
    reverse=s.shift_scores(x[:,::-1],max_dt=2,max_dn=3).query('delta_draw==2 and delta_number==-3').iloc[0]
    assert reverse.observed_matches==row.observed_matches


@pytest.mark.parametrize('dn',[3,-3])
def test_maximal_chains_not_nested(dn):
    s=api(); x=np.zeros((12,45),bool); start=0 if dn>0 else 30
    for k in range(5): x[k*2,start+k*dn]=True
    paths=s.chains(x,max_dt=2,max_dn=3)
    p=paths.query('delta_draw==2 and delta_number==@dn')
    assert len(p)==1 and p.iloc[0].chain_length==5 and p.iloc[0].start_draw==1


def test_hough_finds_known_line():
    s=api(); x=np.zeros((40,45),bool)
    for k in range(20): x[k,2*k]=True
    lines=s.hough_lines(x,max_dt=2,max_dn=2,min_length=12)
    best=lines.iloc[0]
    assert best.delta_draw==1 and best.delta_number==2 and best.support==20
    assert best.density>0.8


def test_surrogate_validity_determinism_and_margins():
    s=api(); x=s.iid_surrogate(70,seed=2)
    assert np.all(x.sum(axis=1)==6)
    assert np.array_equal(x,s.iid_surrogate(70,seed=2))
    y=s.constrained_surrogate(x,seed=12,trades_per_row=10)
    assert np.array_equal(y,s.constrained_surrogate(x,seed=12,trades_per_row=10))
    assert np.array_equal(x.sum(axis=0),y.sum(axis=0))
    assert np.all(y.sum(axis=1)==6) and not np.array_equal(x,y)


def test_global_max_and_complete_search():
    s=api(); x=s.iid_surrogate(30,seed=1)
    cfg=s.SearchConfig(max_dt=3,max_dn=2,hough_dt=2,hough_dn=2,hough_min_length=6)
    real=s.search(x,cfg)
    assert set(real['maxima'])=={'shift','direction','chain','longest_chain','hough','spectrum'}
    comparison,null=s.compare_nulls(x,cfg,replicates=3,seed=19)
    again,null2=s.compare_nulls(x,cfg,replicates=3,seed=19)
    assert null.equals(null2) and comparison.equals(again)
    for row in comparison.itertuples():
        values=null[null.null_model==row.null_model][row.statistic].to_numpy()
        assert row.global_p==pytest.approx((1+(values>=row.real_max).sum())/4)
        assert row.family_adjusted_p==min(1,row.global_p*6)


def test_empty_overlap_safe():
    s=api(); x=np.zeros((3,45),bool)
    scores=s.shift_scores(x,max_dt=2,max_dn=1)
    assert scores.match_rate.isna().all()
    with pytest.raises(ValueError): s.shift_scores(x,max_dt=3,max_dn=1)


def test_fft_overlap_matches_direct_count_and_search_export_does_not_change_maxima():
    s=api(); x=s.iid_surrogate(80,seed=81)
    for row in s.shift_scores(x,max_dt=4,max_dn=3).itertuples():
        source,destination=s.aligned(x,row.delta_draw,row.delta_number)
        assert row.observed_matches==int((source&destination).sum())
        assert row.valid_opportunities==int(source.sum())
    cfg=s.SearchConfig(max_dt=4,max_dn=3,hough_dt=3,hough_dn=3)
    assert s.search(x,cfg,details=True)['maxima']==s.search(x,cfg,details=False)['maxima']


def test_bad_main_rows_rejected(history):
    s=api(); bad=history.copy(); bad.loc[0,'num2']=bad.loc[0,'num1']
    with pytest.raises(ValueError): s.lotto_matrix(bad,cutoff=12)
    with pytest.raises(ValueError): s.lotto_matrix(history,cutoff=1246)


def test_translation_plots_allow_arbitrary_windows(tmp_path):
    from src.spatiotemporal_cli import plot_matrix
    x=api().iid_surrogate(20,seed=12); path=tmp_path/'window.png'
    plot_matrix(x,path,start=5,end=12)
    assert path.read_bytes().startswith(b'\x89PNG')
    with pytest.raises(ValueError): plot_matrix(x,path,start=5,end=21)


def test_rolling_plot_accepts_numeric_csv_displacements(tmp_path):
    import pandas as pd
    from src.spatiotemporal_cli import _plots
    s=api(); cfg=s.SearchConfig(max_dt=3,max_dn=2,hough_dt=2,hough_dn=2)
    x=s.iid_surrogate(30,seed=11); result=s.search(x,cfg)
    comparison,null=s.compare_nulls(x,cfg,replicates=2)
    rolling=pd.DataFrame([dict(delta_draw=3.,delta_number=-2.,end_draw=30.,match_rate=.14)])
    _plots(result,rolling,comparison,null,tmp_path)
    assert (tmp_path/'rolling_translation_strength.png').exists()
