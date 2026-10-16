import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


@pytest.mark.parametrize('name',['TranslationModel','ChainModel'])
def test_prediction_requires_exact_past_and_frozen_prefix(name):
    from src.models import translation
    cls=getattr(translation,name); x=iid_surrogate(130,seed=5)
    model=cls(max_dt=5,max_dn=3).fit(x[:110],cutoff=110)
    scores=model.score_matrix(x[:120],target=121)
    assert set(scores)==set(range(1,46)) and np.isfinite(list(scores.values())).all()
    assert scores==cls(max_dt=5,max_dn=3).fit(x[:110],cutoff=110).score_matrix(x[:120],target=121)
    with pytest.raises(ValueError): model.score_matrix(x[:121],target=121)
    with pytest.raises(ValueError): model.fit(x,cutoff=110)
    changed=x[:120].copy(); changed[0]=np.roll(changed[0],1)
    with pytest.raises(ValueError): model.score_matrix(changed,target=121)


def test_chain_continuation_and_boundaries():
    from src.models.translation import ChainModel
    x=iid_surrogate(120,seed=8)
    x[-4]=False; x[-4,[0,1,2,3,4,5]]=True
    x[-2]=False; x[-2,[3,8,15,25,35,44]]=True
    m=ChainModel(max_dt=3,max_dn=3).fit(x,cutoff=120)
    # Isolate a known learned-rule-shaped fixture to check application, not fitting.
    m.rules=[dict(delta_draw=2,delta_number=3,weight=1.)]
    scores=m.score_matrix(x,target=121)
    assert scores[7]>scores[1] and scores[7]>scores[45]
    assert max(scores.values())<=1 and min(scores.values())>=0


def test_direction_and_time_ablation():
    from src.models.translation import TranslationModel
    x=iid_surrogate(120,seed=42)
    m=TranslationModel(direction='negative',min_dt=3,max_dt=7,max_dn=3).fit(x,cutoff=120)
    assert m.rules and all(r['delta_number']<0 and 3<=r['delta_draw']<=7 for r in m.rules)
    with pytest.raises(ValueError): TranslationModel(direction='up')
    with pytest.raises(ValueError): m.fit(x[:50],cutoff=50)


@pytest.mark.parametrize('model_name',['TranslationModel','ChainModel'])
def test_walk_forward_cutoffs_and_target_poisoning(history,model_name):
    from test_features import extend
    from src.backtest.translation import walk_forward
    from src.models import translation
    from src.analysis.spatiotemporal import lotto_matrix
    data=extend(history,130); factories={model_name:lambda:getattr(translation,model_name)(max_dt=3,max_dn=2)}
    first=walk_forward(data,factories,start=120,end=125,cadence=4)
    assert first[first.model==model_name].training_cutoff.tolist()==[119]*4+[123]*2
    altered=data.copy(); altered.loc[altered.draw_no==125,[f'num{i}' for i in range(1,7)]]=[30,31,32,33,34,35]
    second=walk_forward(altered,factories,start=120,end=125,cadence=4)
    assert first.scores.tolist()==second.scores.tolist()
    assert first.ranking.tolist()==second.ranking.tolist()
    assert (first.feature_cutoff==first.target_draw-1).all()
    with pytest.raises(ValueError): walk_forward(data,factories,start=120,end=1246)


def test_combined_is_rank_average():
    from src.models.translation import combine_scores
    a={n:float(n) for n in range(1,46)}; b={n:46-float(n) for n in range(1,46)}
    assert np.allclose(list(combine_scores(a,b).values()),.5)


def test_pool_comparison_paired_and_exact():
    import pandas as pd
    from src.backtest.translation import pool_report
    rows=[]
    for name in ('RandomModel','Other'):
        for target in range(105,115):
            rows.append(dict(model=name,target_draw=target,**{f'pool_{k}':5 if target==105 else 1 for k in (6,8,10,12,15)}))
    report=pool_report(pd.DataFrame(rows))
    assert (report.paired_delta_5plus==0).all()
    assert (report.paired_ci_low_5plus==0).all() and (report.paired_ci_high_5plus==0).all()
    assert (report.count_5plus==1).all() and (report.count_6plus==0).all()
    assert report[report.pool_size==15].exact_random_5plus.iloc[0]>report[report.pool_size==8].exact_random_5plus.iloc[0]


def test_gap_logistic_compatibility(history):
    import json
    from test_features import extend
    from src.analysis.features import build_features,GAP
    from src.models.predictive import LogisticModel
    from src.models.translation import TranslationModel
    from src.backtest.translation import walk_forward
    data=extend(history,126); features=build_features(data)
    expected=LogisticModel(columns=GAP).fit(features[features.target_draw<120],cutoff=119)
    result=walk_forward(data,{'TranslationModel':lambda:TranslationModel(max_dt=3,max_dn=2)},
        start=120,end=123,cadence=4,gap_features=features)
    for row in result[result.model=='GapLogistic'].itertuples():
        scores=expected.score_rows(features[features.target_draw==row.target_draw].drop(columns='appeared_next'))
        assert json.loads(row.scores)=={str(n):value for n,value in scores.items()}
