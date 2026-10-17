import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate

@pytest.mark.parametrize('name',['FrequencyConditionedTranslationModel','FrequencyConditionedChainModel'])
@pytest.mark.parametrize('window',[10,26,52])
def test_models_causal_seedless_determinism_frozen_bins(name,window):
    from src.models import frequency3d
    cls=getattr(frequency3d,name);x=iid_surrogate(150,seed=9)
    m=cls(window=window,max_dt=3,max_dn=2,min_support=3).fit(x[:120],cutoff=120)
    config=m.encoder.configuration();scores=m.score_matrix(x[:130],target=131)
    assert scores==cls(window=window,max_dt=3,max_dn=2,min_support=3).fit(x[:120],cutoff=120).score_matrix(x[:130],target=131)
    assert set(scores)==set(range(1,46)) and np.isfinite(list(scores.values())).all()
    assert m.encoder.configuration()==config
    with pytest.raises(ValueError): m.score_matrix(x[:131],target=131)
    with pytest.raises(ValueError): m.fit(x[:121],cutoff=120)
    diagnostic=m.explain_number(31,x[:130],target=131)
    assert diagnostic['score']==scores[31] and diagnostic['window']==window
    assert all(r['source_draw']<131 for r in diagnostic['rules'])
    assert all(r['opportunities']>=3 and r['delta_number']!=0 for r in m.rules)

@pytest.mark.parametrize('name',['FrequencyConditionedTranslationModel','FrequencyConditionedChainModel'])
def test_target_poisoning_and_parent_predictions_preserved(history,name):
    from test_features import extend
    from src.models import frequency3d
    from src.models.translation import TranslationModel,ChainModel
    from src.backtest.translation import walk_forward
    data=extend(history,130)
    factories={'TranslationModel':lambda:TranslationModel(max_dt=3,max_dn=2),
               'ChainModel':lambda:ChainModel(max_dt=3,max_dn=2),
               name:lambda:getattr(frequency3d,name)(max_dt=3,max_dn=2,min_support=2)}
    a=walk_forward(data,factories,start=120,end=125,cadence=4,combined=False)
    poisoned=data.copy();poisoned.loc[poisoned.draw_no==125,[f'num{i}' for i in range(1,7)]]=[30,31,32,33,34,35]
    b=walk_forward(poisoned,factories,start=120,end=125,cadence=4,combined=False)
    assert a.scores.tolist()==b.scores.tolist()
    parent=walk_forward(data,{n:f for n,f in factories.items() if n!=name},start=120,end=125,cadence=4,combined=False)
    assert a[a.model!=name].scores.tolist()==parent.scores.tolist()
    assert a[a.model==name].training_cutoff.tolist()==[119]*4+[123]*2

def test_sparse_frequency_rules_fallback_and_scope():
    from src.models.frequency3d import FrequencyConditionedTranslationModel
    x=iid_surrogate(130,seed=4)
    m=FrequencyConditionedTranslationModel(min_support=100000).fit(x,cutoff=130)
    assert m.rules==[] and set(m.score_matrix(x,target=131).values())=={6/45}
    with pytest.raises(ValueError): FrequencyConditionedTranslationModel(window=11)
    with pytest.raises(ValueError): m.fit(iid_surrogate(1246,seed=5),cutoff=1246)
