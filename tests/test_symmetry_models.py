import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.models.symmetry import MirrorModel
from src.models.predictive import rank_numbers


def test_mirror_model_scores_all_numbers_and_center_is_separate():
    x=iid_surrogate(260,seed=18);model=MirrorModel(window=10,lag=3,shrinkage=50).fit(x,cutoff=260)
    scores=model.score_matrix(x,target=261)
    assert sorted(scores)==list(range(1,46)) and np.isfinite(list(scores.values())).all()
    assert scores[23]==6/45
    assert model.score_training_cutoff==260
    assert all(r['source_draw']==258 and r['training_cutoff']==260 for r in model.last_diagnostic)
    assert model.last_diagnostic[37]['mirror']==8
    assert model.last_diagnostic[22]['contribution']==0
    assert sorted(rank_numbers(scores))==list(range(1,46))


def test_future_rows_target1246_and_wrong_training_cutoff_are_rejected():
    x=iid_surrogate(300,seed=19);model=MirrorModel().fit(x[:260],cutoff=260)
    with pytest.raises(ValueError):model.score_matrix(x,target=261)
    with pytest.raises(ValueError):MirrorModel().fit(x,cutoff=299)
    with pytest.raises(ValueError):model.score_matrix(iid_surrogate(1245,seed=1),target=1246)
    with pytest.raises(ValueError):MirrorModel().fit(np.vstack([x]*5),cutoff=1500)


def test_outer_cadence_cannot_freeze_components_or_use_future_normalization():
    x=iid_surrogate(300,seed=21)
    early=MirrorModel(window=26,lag=8).fit(x[:260],cutoff=260)
    fresh=MirrorModel(window=26,lag=8).fit(x[:280],cutoff=280)
    a=early.score_matrix(x[:280],target=281);b=fresh.score_matrix(x[:280],target=281)
    assert a==b and early.score_training_cutoff==280
    changed=x[:280].copy();changed[0]=x[1]
    with pytest.raises(ValueError):early.score_matrix(changed,target=281)
    assert early.score_matrix(x[:280],target=281)==a


def test_planted_reflection_relation_has_positive_pooled_coefficient():
    base=iid_surrogate(150,seed=22);x=np.empty((300,45),dtype=bool)
    x[::2]=base;x[1::2]=base[:,::-1]
    model=MirrorModel(window=10,lag=1,shrinkage=50).fit(x,cutoff=300)
    model.score_matrix(x,target=301)
    assert model.pooled_coefficient>0
    for row in model.last_diagnostic:
        if row['number']!=23:
            assert row['mirror']==46-row['number']
            assert row['score']==pytest.approx(6/45+row['contribution'])


def test_constant_history_has_no_spurious_learned_coefficient():
    x=np.zeros((260,45),dtype=bool);x[:,:6]=True
    m=MirrorModel().fit(x,cutoff=260);scores=m.score_matrix(x,target=261)
    assert m.pooled_coefficient==0 and set(scores.values())=={6/45}


@pytest.mark.parametrize('kwargs',[dict(window=11),dict(lag=0),dict(lag=True),dict(shrinkage=51),dict(support=0)])
def test_model_grid_is_bounded(kwargs):
    with pytest.raises(ValueError):MirrorModel(**kwargs)
