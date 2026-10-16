import pandas as pd
import pytest
from test_features import extend
from src.analysis.features import build_features, build_prospective_features
from src.prediction_scope import ProspectiveScope
from src.models.predictive import LogisticModel
from src.analysis.features import GAP


def test_scoped_features_identical_and_target_unlabeled(history):
    data=extend(history,110)
    scoped=build_prospective_features(data,scope=ProspectiveScope(110))
    old=build_features(data,include_current=True)
    pd.testing.assert_frame_equal(old,scoped)
    assert scoped[scoped.target_draw==111].appeared_next.isna().all()
    assert scoped[scoped.target_draw==111].feature_cutoff.eq(110).all()


def test_scope_rejects_future_history_and_target_labels(history):
    with pytest.raises(ValueError): build_prospective_features(extend(history,111),scope=ProspectiveScope(110))
    with pytest.raises(ValueError): ProspectiveScope(1246)
    features=build_prospective_features(extend(history,110),scope=ProspectiveScope(110))
    training=features[features.target_draw<=110]
    current=features[features.target_draw==111]
    model=LogisticModel(columns=GAP,prediction_scope=ProspectiveScope(110)).fit(training,cutoff=110)
    with pytest.raises(ValueError): model.score_rows(current)
    with pytest.raises(ValueError): model.fit(features.fillna(0),cutoff=110)
    with pytest.raises(ValueError): model.score_rows(current.drop(columns='appeared_next').assign(target_draw=112,feature_cutoff=111))
    normal=LogisticModel(columns=GAP).fit(training,cutoff=110)
    assert model.score_rows(current.drop(columns='appeared_next'))==normal.score_rows(current.drop(columns='appeared_next'))


def test_1245_scope_is_explicit_and_does_not_change_research_seal():
    from test_regime_models import rows
    data=rows(105).assign(has_appeared=1,median_gap=7.5)
    data.target_draw+=1036; data.feature_cutoff+=1036  #1141-1245
    with pytest.raises(ValueError,match='sealed'): LogisticModel(columns=GAP).fit(data,cutoff=1245)
    model=LogisticModel(columns=GAP,prediction_scope=ProspectiveScope(1245)).fit(data,cutoff=1245)
    current=data[data.target_draw==1245].drop(columns='appeared_next').assign(target_draw=1246,feature_cutoff=1245)
    assert len(model.score_rows(current))==45
