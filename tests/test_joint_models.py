import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate

@pytest.mark.parametrize('name',['JointStateTranslationModel','JointStateChainModel','JointStateFrequencyBaseline'])
def test_three_joint_models_causal_deterministic_frozen_encoder(name):
    from src.models import joint
    cls=getattr(joint,name);x=iid_surrogate(150,seed=9)
    kwargs={} if name.endswith('Baseline') else dict(max_dt=3,max_dn=2,min_support=3)
    m=cls(**kwargs).fit(x[:120],cutoff=120);cfg=m.encoder.configuration()
    scores=m.score_matrix(x[:130],target=131)
    assert scores==cls(**kwargs).fit(x[:120],cutoff=120).score_matrix(x[:130],target=131)
    assert set(scores)==set(range(1,46)) and np.isfinite(list(scores.values())).all()
    assert m.encoder.configuration()==cfg
    with pytest.raises(ValueError):m.score_matrix(x[:131],target=131)
    with pytest.raises(ValueError):m.fit(x[:121],cutoff=120)
    explanation=m.explain_number(31,x[:130],target=131)
    assert explanation['score']==scores[31]
    if not name.endswith('Baseline'):
        assert all(r['source_draw']<131 and 'gap_opportunities' in r and 'frequency_opportunities' in r for r in explanation['rules'])

def test_frequency_baseline_label_alignment_and_shrinkage():
    from src.models.joint import JointStateFrequencyBaseline
    x=iid_surrogate(130,seed=4);m=JointStateFrequencyBaseline().fit(x,cutoff=130)
    state=m.encoder.transform(x)['joint_state'][:-1]
    for s in range(9):
        assert m.observations[s]==(state==s).sum() and m.positives[s]==(x&(state==s)).sum()
        expected=(m.positives[s]+100*6/45)/(m.observations[s]+100) if m.observations[s]>=100 else 6/45
        assert m.posterior[s]==pytest.approx(expected)
    sparse=JointStateFrequencyBaseline(min_support=100000).fit(x,cutoff=130)
    assert set(sparse.score_matrix(x,target=131).values())=={6/45}

@pytest.mark.parametrize('name',['JointStateTranslationModel','JointStateChainModel','JointStateFrequencyBaseline'])
def test_walkforward_target_poisoning_parent_reproduction(history,name):
    from test_features import extend
    from src.models import joint
    from src.models.translation import TranslationModel
    from src.backtest.translation import walk_forward
    d=extend(history,130);kwargs={} if name.endswith('Baseline') else dict(max_dt=3,max_dn=2,min_support=2)
    factories={'TranslationModel':lambda:TranslationModel(max_dt=3,max_dn=2),name:lambda:getattr(joint,name)(**kwargs)}
    a=walk_forward(d,factories,start=120,end=125,cadence=4,combined=False)
    b=d.copy();b.loc[b.draw_no==125,[f'num{i}' for i in range(1,7)]]=[30,31,32,33,34,35]
    c=walk_forward(b,factories,start=120,end=125,cadence=4,combined=False)
    assert a.scores.tolist()==c.scores.tolist()
    only=walk_forward(d,{'TranslationModel':factories['TranslationModel']},start=120,end=125,cadence=4,combined=False)
    assert a[a.model!=name].scores.tolist()==only.scores.tolist()
    assert a[a.model==name].training_cutoff.tolist()==[119]*4+[123]*2
