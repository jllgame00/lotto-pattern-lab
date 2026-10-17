import pandas as pd
import pytest

def fixtures():
    rows=[]
    for prefix in ('FrequencyConditionedTranslationModel','FrequencyConditionedChainModel'):
        for w in (10,26,52):
            for t in range(880,921):
                rows.append(dict(model=prefix+('' if w==26 else f'_W{w}'),target_draw=t,hits=int(w==10)))
    return pd.DataFrame(rows)

def test_window_selection_development_only_and_frozen():
    from src.backtest.frequency3d import select_development_windows
    frame=fixtures();before=select_development_windows(frame,development_start=880)
    frame.loc[frame.target_draw>900,'hits']=1000
    assert select_development_windows(frame,development_start=880)==before
    assert all(v['window']==10 and v['training_selection_cutoff']==900 for v in before.values())
    frame['hits']=0
    assert all(v['window']==26 for v in select_development_windows(frame,development_start=880).values())
    with pytest.raises(ValueError): select_development_windows(frame.iloc[1:],development_start=880)

def test_paired_three_references_require_identical_targets():
    from src.backtest.frequency3d import paired_comparisons
    names=['FrequencyConditionedTranslationModel','RandomModel','TranslationModel','GapConditionedTranslationModel']
    rows=[]
    for name in names:
        for t in range(401,431):
            value=int(name.startswith('Frequency'))
            rows.append(dict(model=name,target_draw=t,hits=value,mean_winning_rank=20-value,
                recall_6=value/6,recall_10=value/6,recall_15=value/6,**{f'pool_{k}':value for k in (8,10,12,15)}))
    frame=pd.DataFrame(rows);result=paired_comparisons(frame,starts=(401,),replicates=20)
    h=result[result.metric=='hits']
    assert set(h.reference)==set(names[1:]) and h.difference.eq(1).all() and h.ci_low.eq(1).all()
    with pytest.raises(ValueError): paired_comparisons(frame.iloc[:-1],starts=(401,),replicates=20)

def test_phase8_report_namespace_protects_all_prior_phases():
    from src.frequency_cli import guard_reports
    from src.prospective_experiment import ROOT
    for path in (ROOT/'data',ROOT/'reports',ROOT/'reports/spatiotemporal3d',ROOT/'reports/prospective/phase7'):
        with pytest.raises(ValueError): guard_reports(path)
