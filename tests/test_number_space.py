"""Hand-checked finite-axis and causal contracts, not visual pattern tests."""
import numpy as np
import pytest
from src.analysis.number_space import (ranges, recent_density, smooth, kernel_matrix,
    draw_statistics, group_zones, movement, range_history, search_space)


@pytest.mark.parametrize('width,count,last',[(3,43,(43,45)),(5,41,(41,45)),(7,39,(39,45)),(9,37,(37,45))])
def test_range_enumeration_covers_both_edges(width,count,last):
    r=ranges(width)
    assert len(r)==count and tuple(r[0])==(1,width) and tuple(r[-1])==last


@pytest.mark.parametrize('window',[10,26,52])
def test_density_uses_completed_draws_and_rejects_target(window):
    x=np.zeros((window,45),bool);x[:,:6]=True
    d=recent_density(x,target=window+1,window=window,width=3)
    assert d.iloc[0]['occurrences']==window*3
    assert d.iloc[0]['density']==1 and d.iloc[-1]['density']==0
    with pytest.raises(ValueError):recent_density(x,target=window,window=window,width=3)
    with pytest.raises(ValueError):recent_density(x[:-1],target=window,window=window,width=3)
    h=range_history(x,window=window,width=3)
    assert h['end_draw'].unique().tolist()==[window]
    assert h['target_draw'].unique().tolist()==[window+1]


def test_smoothing_normalizes_at_edges_without_wrap_and_excludes_center():
    a=np.zeros(45);a[0]=1
    s=smooth(a,'triangular1')
    assert s[0]==pytest.approx(2/3) and s[1]==pytest.approx(.25) and s[-1]==0
    neighbors=smooth(a,'triangular1',neighbor_only=True)
    assert neighbors[0]==0 and neighbors[1]==pytest.approx(.5)
    assert np.allclose(smooth(np.ones(45),'gaussian2'),1)
    for k in ('none','triangular1','triangular2','gaussian2','box1','box2','box3','box4'):
        m=kernel_matrix(k);assert np.allclose(m.sum(axis=1),1)
    with pytest.raises(ValueError):smooth(a,'none',neighbor_only=True)


def test_spacing_and_regions_are_main_numbers_only():
    x=np.zeros((2,45),bool);x[:,[0,1,3,9,19,44]]=True
    s=draw_statistics(x).iloc[0]
    assert s['adjacent_spacings']==[1,2,6,10,25]
    assert s['minimum_spacing']==1 and s['maximum_spacing']==25
    assert s['draw_range']==44 and s['consecutive_pairs']==1
    assert s['gaps_le2']==2 and s['gaps_ge10']==2
    assert s['clusters_2']==4 and s['clusters_4']==4
    assert [s[f'region_{i}'] for i in range(5)]==[3,1,1,0,1]


def test_overlapping_hot_ranges_are_one_zone_and_movement_is_explicit():
    assert group_zones([(21,25),(22,26),(23,27),(39,43)])==[(21,27),(39,43)]
    m=movement(np.array([12,14,16,18,18,15]),width=5)
    assert m['direction_run']==3 and m['positive_2_run']==3
    assert m['identical_run']==2 and m['mean_abs_movement']==pytest.approx(1.8)
    assert m['overlap_mean']<1


def test_search_space_counts_actual_finite_windows():
    s=search_space(60)
    assert s['range_density_cells']==(51+35+9)*160
    assert s['kernel_cells']==(51+35+9)*45*15
    assert s['motif_universe']==1086008
