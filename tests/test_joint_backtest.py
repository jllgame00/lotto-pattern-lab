import copy
import pandas as pd
import pytest

def test_frozen_development_protocol_rejects_later_tuning():
    from src.backtest.joint import frozen_protocol,validate_frozen_protocol
    before=frozen_protocol();after=copy.deepcopy(before)
    validate_frozen_protocol(before,after)
    assert before['development_end']==900 and before['later_start']==901
    after['configurations']['JointStateTranslationModel']['min_support']=10
    with pytest.raises(ValueError):validate_frozen_protocol(before,after)

def test_joint_paired_references_and_geometry_baseline():
    from src.backtest.joint import paired_comparisons
    names=['JointStateTranslationModel','RandomModel','TranslationModel','GapConditionedTranslationModel',
           'FrequencyConditionedTranslationModel','JointStateFrequencyBaseline'];rows=[]
    for name in names:
        for t in range(401,431):
            v=int(name=='JointStateTranslationModel')
            rows.append(dict(model=name,target_draw=t,hits=v,mean_winning_rank=20-v,
                recall_6=v/6,recall_10=v/6,recall_15=v/6,**{f'pool_{k}':v for k in (8,10,12,15)}))
    result=paired_comparisons(pd.DataFrame(rows),starts=(401,),replicates=20)
    h=result.query('model=="JointStateTranslationModel" and metric=="hits"')
    assert set(h.reference)==set(names[1:]) and h.difference.eq(1).all() and h.ci_low.eq(1).all()
    with pytest.raises(ValueError):paired_comparisons(pd.DataFrame(rows).iloc[:-1],starts=(401,),replicates=20)

def test_joint_report_directory_protection():
    from src.joint_cli import guard_reports
    from src.prospective_experiment import ROOT
    for p in (ROOT/'data',ROOT/'reports',ROOT/'reports/spatiotemporal_frequency',ROOT/'reports/prospective/phase8'):
        with pytest.raises(ValueError):guard_reports(p)

def test_joint_complete_pipeline_short_history(history,tmp_path):
    from test_features import extend
    from src.joint_cli import analyze
    meta=analyze(extend(history,120),tmp_path/'joint_reports',replicates=1,progress=None)
    assert meta['search_space']['joint_translations']==14508 and not meta['future_result_accessed']
    assert (tmp_path/'joint_reports/plots/joint_support.png').is_file()
