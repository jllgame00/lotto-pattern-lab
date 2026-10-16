import numpy as np
import pandas as pd
import pytest


def test_prior_report_directories_are_protected():
    from src.gap3d_cli import guard_reports
    from src.prospective_experiment import ROOT
    for path in (ROOT/'reports/spatiotemporal',ROOT/'reports/prospective/phase6',ROOT/'reports',ROOT/'data/raw'):
        with pytest.raises(ValueError): guard_reports(path)
    guard_reports(ROOT/'reports/spatiotemporal3d')


def test_paired_parent_alignment_and_intervals():
    from src.backtest.gap3d import paired_comparisons
    rows=[]
    for model,hits in [('TranslationModel',0),('RandomModel',0),('GapConditionedTranslationModel',1)]:
        for draw in range(401,431):
            rows.append(dict(model=model,target_draw=draw,hits=hits,mean_winning_rank=20-hits,
                recall_6=hits/6,recall_10=hits/6,recall_15=hits/6,**{f'pool_{k}':hits for k in (6,8,10,12,15)}))
    result=paired_comparisons(pd.DataFrame(rows),starts=(401,),replicates=20)
    hits=result[result.metric=='hits']
    assert set(hits.reference)=={'TranslationModel','RandomModel'}
    assert (hits.difference==1).all() and (hits.ci_low==1).all() and (hits.ci_high==1).all()
    with pytest.raises(ValueError): paired_comparisons(pd.DataFrame(rows).iloc[:-1],starts=(401,),replicates=20)


def test_complete_descriptive_pipeline_synthetic(history,tmp_path):
    from test_features import extend
    from src.gap3d_cli import analyze
    metadata=analyze(extend(history,120),tmp_path/'phase7reports',replicates=1,progress=None)
    assert metadata['future_result_accessed'] is False
    assert (tmp_path/'phase7reports'/'plots'/'high_gap_shifts.png').exists()
    assert (tmp_path/'phase7reports'/'global_null_comparison.csv').exists()
