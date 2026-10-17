import numpy as np
import pandas as pd
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.models.number_space import RangeDensityModel,NeighborhoodModel,rank_mix
from src.backtest.number_space import select_development


@pytest.mark.parametrize('factory',[RangeDensityModel,NeighborhoodModel])
def test_model_requires_unchanged_past_only_and_is_deterministic(factory):
    x=iid_surrogate(120,seed=1);m=factory().fit(x[:104],cutoff=104)
    a=m.score_matrix(x[:110],target=111)
    assert len(a)==45 and np.isfinite(list(a.values())).all()
    assert a==factory().fit(x[:104],cutoff=104).score_matrix(x[:110],target=111)
    with pytest.raises(ValueError):m.score_matrix(x[:111],target=111)
    changed=x[:110].copy();changed[0]=x[2]
    with pytest.raises(ValueError):m.score_matrix(changed,target=111)
    with pytest.raises(ValueError):factory().fit(x[:110],cutoff=109)


def test_neighborhood_neighbor_only_distinguishes_own_from_neighbors():
    x=np.zeros((104,45),bool);x[:,[0,10,20,30,40,44]]=True
    own=NeighborhoodModel(kernel='none').fit(x,cutoff=104).score_matrix(x,target=105)
    neighbor=NeighborhoodModel(kernel='triangular1',neighbor_only=True).fit(x,cutoff=104).score_matrix(x,target=105)
    assert own[1]==1 and own[2]==0
    assert neighbor[1]==0 and neighbor[2]==.5 and neighbor[45]==0
    assert rank_mix(own,neighbor,.5)==rank_mix(own,neighbor,.5)


def test_development_selection_rejects_later_outcomes_and_breaks_ties_stably():
    rows=pd.DataFrame([dict(model='first',target_draw=401,hits=1),dict(model='second',target_draw=401,hits=1)])
    assert select_development(rows,['first','second'],end=900)=='first'
    with pytest.raises(ValueError):select_development(pd.concat([rows,rows.assign(target_draw=901)]),['first','second'],end=900)
    with pytest.raises(ValueError):select_development(rows.iloc[:1],['first','second'],end=900)


def test_gap_combination_keeps_training_scaler_fixed_and_rejects_future_rows(history):
    from test_features import extend
    from src.analysis.features import build_prospective_features
    from src.prediction_scope import ProspectiveScope
    from src.analysis.spatiotemporal import lotto_matrix
    from src.models.number_space import GapNeighborhoodModel
    data=extend(history,120);x=lotto_matrix(data,cutoff=120)
    features=build_prospective_features(data,scope=ProspectiveScope(120))
    training=features[features.target_draw<=115]
    current=features[features.target_draw==121].drop(columns='appeared_next')
    m=GapNeighborhoodModel(window=26,kernel='triangular2',gap_weight=.75).fit(x[:115],cutoff=115,feature_rows=training)
    means=m.gap.transformer.means.copy();score=m.score_matrix(x,target=121,current_rows=current)
    assert len(score)==45 and np.array_equal(means,m.gap.transformer.means)
    with pytest.raises(ValueError):m.score_matrix(x,target=120,current_rows=current)
    with pytest.raises(ValueError):GapNeighborhoodModel().fit(x[:115],cutoff=115,feature_rows=features[features.target_draw<=116])
