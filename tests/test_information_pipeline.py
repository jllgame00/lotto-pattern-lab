import json
import numpy as np
import pandas as pd
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.backtest.information_flow import select_development,configuration_hash,load_selection,candidates,rank_diversity
from src.phase13_freeze import prepare_freeze,PENDING


def test_development_selection_rejects_later_targets_and_mismatched_sets():
    rows=pd.DataFrame([dict(candidate=c,target_draw=t,hits=h) for c,h in [('a',1),('b',2)] for t in (899,900)])
    assert select_development(rows)=='b'
    with pytest.raises(ValueError):select_development(rows.assign(target_draw=[899,900,900,901]))
    with pytest.raises(ValueError):select_development(rows.iloc[:-1])
    assert len(candidates())==70


def test_frozen_selection_integrity_and_fixed_ranges(tmp_path):
    specs=candidates();mi=next(c for c in specs.values() if c['model']=='MutualInformationModel')
    te=next(c for c in specs.values() if c['model']=='TransferEntropyModel')
    s=dict(version='phase13-v1',research_cutoff=1245,development_end=900,later_start=901,candidate_count=70,
        models={'MutualInformationModel':mi,'TransferEntropyModel':te})
    p=tmp_path/'selected.json';p.write_text(json.dumps(dict(selection=s,sha256=configuration_hash(s))))
    assert load_selection(p)==s
    s['models']['TransferEntropyModel']['lag']=1246
    p.write_text(json.dumps(dict(selection=s,sha256=configuration_hash(s))))
    with pytest.raises(ValueError):load_selection(p)


def test_rank_diversity_aligns_number_coordinates():
    a=list(range(1,46))
    assert rank_diversity(a,a)['spearman']==pytest.approx(1)
    assert rank_diversity(a,a[::-1])['spearman']==pytest.approx(-1)
    assert rank_diversity(a,a[::-1])['top6_overlap']==0


def test_archive_absent_blocks_and_target1246_refused(tmp_path):
    p=tmp_path/'selected.json';p.write_text('{}')
    with pytest.raises(ValueError,match=PENDING):prepare_freeze(p,tmp_path/'absent')
    with pytest.raises(ValueError):prepare_freeze(p,tmp_path/'absent',target=1246)
    assert list(tmp_path.iterdir())==[p]


def test_no_phase13_parse_of_draw1246_and_output_guard(tmp_path):
    from pathlib import Path
    from src.information_cli import load_research_source,guard
    raw=Path('data/raw/lotto_history.csv').read_bytes();p=tmp_path/'future.csv'
    p.write_bytes(raw+b'1246,UNREADABLE_FUTURE_SUFFIX\xff\n')
    with pytest.raises(ValueError,match='unknown suffix'):load_research_source(p)
    with pytest.raises(ValueError):guard('reports/prospective')


def test_invalid_analysis_arguments_write_nothing(tmp_path):
    from src.information_cli import analyze
    for n,w in ((0,1),(1,0)):
        with pytest.raises(ValueError):analyze(iid_surrogate(1245,seed=8),tmp_path,n,w)
        assert list(tmp_path.iterdir())==[]


def test_information_tables_use_exact_900_901_1245_prefixes(monkeypatch):
    import src.models.information_flow as module
    x=iid_surrogate(1245,seed=82);mi_inputs=[];te_inputs=[]
    original_mi=module.mi_matrix;original_te=module.te_matrix
    def trace_mi(values,*args,**kwargs):
        mi_inputs.append(values.copy());return original_mi(values,*args,**kwargs)
    def trace_te(values,*args,**kwargs):
        te_inputs.append(values.copy());return original_te(values,*args,**kwargs)
    monkeypatch.setattr(module,'mi_matrix',trace_mi);monkeypatch.setattr(module,'te_matrix',trace_te)
    for target in (901,1245):
        module._mi_matrix_cache.cache_clear();module._te_matrix_cache.cache_clear()
        mi_inputs.clear();te_inputs.clear()
        for cls in (module.MutualInformationModel,module.TransferEntropyModel):
            model=cls().fit(x[:900],cutoff=900);model.score_matrix(x[:target-1],target=target)
            with pytest.raises(ValueError):model.score_matrix(x,target=target)
        expected=x[target-1-624:target-1]
        assert len(mi_inputs)==1 and np.array_equal(mi_inputs[0],expected)
        assert len(te_inputs)==1 and np.array_equal(te_inputs[0],expected)


def test_walk_forward_information_fit_boundaries():
    from src.models.information_flow import MutualInformationModel
    from src.backtest.translation import walk_forward
    from src.collect.dataset import MAIN_COLUMNS
    x=iid_surrogate(903,seed=27);numbers=np.array([np.flatnonzero(row)+1 for row in x])
    history=pd.DataFrame(numbers,columns=MAIN_COLUMNS)
    history['draw_no']=np.arange(1,904)
    history['draw_date']=pd.date_range('2002-12-07',periods=903,freq='7D').strftime('%Y-%m-%d')
    history['bonus']=[next(n for n in range(1,46) if n not in row) for row in numbers]
    audit=[]
    class TracedMI(MutualInformationModel):
        def fit(self,past,*,cutoff):
            audit.append(('fit',len(past),cutoff));return super().fit(past,cutoff=cutoff)
        def score_matrix(self,past,*,target):
            audit.append(('score',len(past),target-1));return super().score_matrix(past,target=target)
    rows=walk_forward(history,{'MutualInformationModel':TracedMI},start=901,end=903,cadence=2,combined=False)
    assert audit==[('fit',900,900),('score',900,900),('score',901,901),('fit',902,902),('score',902,902)]
    assert (rows.feature_cutoff==rows.target_draw-1).all() and (rows.training_cutoff<rows.target_draw).all()
    from src.backtest.information_flow import annotate_information_cutoffs
    rows=annotate_information_cutoffs(rows)
    information=rows[rows.model=='MutualInformationModel']
    assert information.training_cutoff.tolist()==[900,901,902]
    assert information.information_training_cutoff.tolist()==[900,901,902]
    assert information.outer_fit_cutoff.tolist()==[900,900,902]


def test_conditional_logloss_compares_source_added_with_own_history():
    from src.backtest.information_flow import conditional_report
    rows=[]
    for target in (1243,1244,1245):
        for model,p in [('TransferEntropyModel',.2),('TargetHistoryBaseline',6/45)]:
            rows.append(dict(target_draw=target,model=model,scores=json.dumps(dict.fromkeys(range(1,46),p)),actual=json.dumps([1,2,3,4,5,6])))
    losses,summary=conditional_report(pd.DataFrame(rows),replicates=50)
    assert (losses.difference>0).all() and len(summary)==3
    assert (summary.ci_low>0).all()


def test_information_flow_cli_exists():
    from src.cli import _parser
    args=_parser().parse_args(['information-flow','prepare-freeze'])
    assert args.action=='prepare-freeze'
