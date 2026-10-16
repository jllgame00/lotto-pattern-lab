import json
import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


@pytest.mark.parametrize('name',['GapConditionedTranslationModel','GapConditionedChainModel'])
def test_models_causal_deterministic_and_frozen_bins(name):
    from src.models import gap3d
    cls=getattr(gap3d,name); x=iid_surrogate(150,seed=9)
    model=cls(max_dt=3,max_dn=2,min_support=5).fit(x[:120],cutoff=120)
    enc=model.encoder.configuration(); scores=model.score_matrix(x[:130],target=131)
    assert scores==cls(max_dt=3,max_dn=2,min_support=5).fit(x[:120],cutoff=120).score_matrix(x[:130],target=131)
    assert set(scores)==set(range(1,46)) and np.isfinite(list(scores.values())).all()
    assert model.encoder.configuration()==enc and enc['training_cutoff']==120
    with pytest.raises(ValueError): model.score_matrix(x[:131],target=131)
    with pytest.raises(ValueError): model.fit(x[:121],cutoff=120)
    assert model.configuration()['destination_state_used'] is False
    diagnostic=model.explain_number(25,x[:130],target=131)
    assert diagnostic['score']==scores[25] and diagnostic['target_draw']==131
    assert all(r['source_draw']<131 for r in diagnostic['rules'])


@pytest.mark.parametrize('representation',['quantile','clipped','relative'])
def test_representation_support_and_training_only_rules(representation):
    from src.models.gap3d import GapConditionedTranslationModel
    x=iid_surrogate(140,seed=82)
    model=GapConditionedTranslationModel(representation=representation,max_dt=3,max_dn=2,min_support=50).fit(x,cutoff=140)
    assert all(r['opportunities']>=50 and r['gap_state']>=0 for r in model.rules)
    assert model.configuration()['representation']==representation
    sparse=GapConditionedTranslationModel(representation=representation,max_dt=3,max_dn=2,min_support=100000).fit(x,cutoff=140)
    assert sparse.rules==[] and set(sparse.score_matrix(x,target=141).values())=={6/45}


@pytest.mark.parametrize('name',['GapConditionedTranslationModel','GapConditionedChainModel'])
def test_walkforward_target_poisoning_and_2d_parent_equality(history,name):
    from test_features import extend
    from src.models import gap3d
    from src.models.translation import TranslationModel,ChainModel
    from src.backtest.translation import walk_forward
    data=extend(history,130)
    factories={'TranslationModel':lambda:TranslationModel(max_dt=3,max_dn=2),
        'ChainModel':lambda:ChainModel(max_dt=3,max_dn=2),name:lambda:getattr(gap3d,name)(max_dt=3,max_dn=2,min_support=5)}
    original=walk_forward(data,factories,start=120,end=125,cadence=4,combined=False)
    changed=data.copy(); changed.loc[changed.draw_no==125,[f'num{i}' for i in range(1,7)]]=[30,31,32,33,34,35]
    poisoned=walk_forward(changed,factories,start=120,end=125,cadence=4,combined=False)
    assert original.scores.tolist()==poisoned.scores.tolist()
    parents=walk_forward(data,{n:f for n,f in factories.items() if n!=name},start=120,end=125,cadence=4,combined=False)
    assert original[original.model!=name].scores.tolist()==parents.scores.tolist()
    assert original[original.model==name].training_cutoff.tolist()==[119]*4+[123]*2
