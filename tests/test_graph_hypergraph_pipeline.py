import json
import numpy as np
import pandas as pd
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.models.graph_hypergraph import GraphStructureModel,HypergraphModel
from src.backtest.graph_hypergraph import select_development,configuration_hash,load_selection,candidates,rank_diversity
from src.phase14_freeze import prepare_freeze,PENDING


@pytest.mark.parametrize('cls',[GraphStructureModel,HypergraphModel])
def test_structural_models_exact_prefix_leakage_guards(cls):
    x=iid_surrogate(240,seed=20);m=cls().fit(x,cutoff=240)
    scores=m.score_matrix(x,target=241)
    assert set(scores)==set(range(1,46)) and np.isfinite(list(scores.values())).all()
    assert scores==cls().fit(x.copy(),cutoff=240).score_matrix(x.copy(),target=241)
    changed=x.copy();changed[0]=iid_surrogate(2,seed=33)[0]
    with pytest.raises(ValueError):m.score_matrix(changed,target=241)
    with pytest.raises(ValueError):m.fit(x,cutoff=239)
    with pytest.raises(ValueError):m.score_matrix(x,target=242)
    with pytest.raises(ValueError):m.score_matrix(iid_surrogate(1245,seed=2),target=1246)
    with pytest.raises(ValueError):cls().fit(iid_surrogate(1246,seed=2),cutoff=1246)


def test_development_only_selection_and_target_parity():
    rows=pd.DataFrame([dict(candidate=c,target_draw=t,hits=h) for c,h in [('a',1),('b',2)] for t in (899,900)])
    assert select_development(rows)=='b'
    with pytest.raises(ValueError):select_development(rows.assign(target_draw=[899,900,900,901]))
    with pytest.raises(ValueError):select_development(rows.iloc[:-1])
    specs=candidates()
    assert len(specs)==30
    assert sum(c['model']=='GraphStructureModel' for c in specs.values())==18


def test_frozen_selection_rejects_outside_search_config(tmp_path):
    specs=candidates();g=next(c for c in specs.values() if c['model']=='GraphStructureModel')
    h=next(c for c in specs.values() if c['model']=='HypergraphModel')
    s=dict(version='phase14-v1',research_cutoff=1245,development_end=900,later_start=901,candidate_count=30,
        models={'GraphStructureModel':g,'HypergraphModel':h})
    p=tmp_path/'selected.json';p.write_text(json.dumps(dict(selection=s,sha256=configuration_hash(s))))
    assert load_selection(p)==s
    s['models']['HypergraphModel']['window']=1246
    p.write_text(json.dumps(dict(selection=s,sha256=configuration_hash(s))))
    with pytest.raises(ValueError):load_selection(p)


def test_rank_diversity_aligns_number_coordinates():
    a=list(range(1,46))
    assert rank_diversity(a,a)['spearman']==pytest.approx(1)
    assert rank_diversity(a,a[::-1])['spearman']==pytest.approx(-1)
    assert rank_diversity(a,a[::-1])['top6_overlap']==0


def test_archive_absent_blocks_publication_and_target1246(tmp_path):
    p=tmp_path/'selected.json';p.write_text('{}')
    with pytest.raises(ValueError,match=PENDING):prepare_freeze(p,tmp_path/'absent')
    with pytest.raises(ValueError):prepare_freeze(p,tmp_path/'absent',target=1246)
    assert list(tmp_path.iterdir())==[p]


def test_source_rejects_future_suffix_and_wrong_output_directory(tmp_path):
    from pathlib import Path
    from src.graph_hypergraph_cli import load_research_source,guard,analyze
    p=tmp_path/'future.csv';p.write_bytes(Path('data/raw/lotto_history.csv').read_bytes()+b'1246,UNREADABLE_FUTURE\xff\n')
    with pytest.raises(ValueError,match='unknown suffix'):load_research_source(p)
    with pytest.raises(ValueError):guard('reports/prospective')
    empty=tmp_path/'out';empty.mkdir()
    for n,w in ((0,1),(1,0)):
        with pytest.raises(ValueError):analyze(iid_surrogate(1245,seed=8),empty,n,w)
        assert list(empty.iterdir())==[]


@pytest.mark.parametrize('cls',[GraphStructureModel,HypergraphModel])
def test_scores_remove_linear_own_frequency(cls):
    x=iid_surrogate(240,seed=73);m=cls(window=52).fit(x,cutoff=240)
    score=np.array(list(m.score_matrix(x,target=241).values()))
    f=x[-52:].sum(0)
    assert abs(score.sum())<1e-9 and abs(score@(f-f.mean()))<1e-8


def test_actual_graph_and_subset_inputs_are_prefixes_901_1245(monkeypatch):
    import src.models.graph_hypergraph as module
    x=iid_surrogate(1245,seed=79);g_inputs=[];h_inputs=[]
    original_g=module.graph;original_h=module.continuation_scores
    def trace_g(values,**kwargs):
        g_inputs.append(values.copy());return original_g(values,**kwargs)
    def trace_h(values,**kwargs):
        h_inputs.append(values.copy());return original_h(values,**kwargs)
    monkeypatch.setattr(module,'graph',trace_g);monkeypatch.setattr(module,'continuation_scores',trace_h)
    for target in (901,1245):
        module._graph_context.cache_clear();module._hyper_context.cache_clear();g_inputs.clear();h_inputs.clear()
        for cls in (GraphStructureModel,HypergraphModel):
            model=cls().fit(x[:900],cutoff=900);model.score_matrix(x[:target-1],target=target)
            with pytest.raises(ValueError):model.score_matrix(x,target=target)
        assert len(g_inputs)==1 and np.array_equal(g_inputs[0],x[:target-1])
        assert len(h_inputs)==1 and np.array_equal(h_inputs[0],x[:target-1])


def test_walk_forward_actual_and_outer_cutoffs():
    from src.backtest.translation import walk_forward
    from src.backtest.graph_hypergraph import annotate_cutoffs
    from src.collect.dataset import MAIN_COLUMNS
    x=iid_surrogate(903,seed=27);numbers=np.array([np.flatnonzero(row)+1 for row in x])
    history=pd.DataFrame(numbers,columns=MAIN_COLUMNS);history['draw_no']=np.arange(1,904)
    history['draw_date']=pd.date_range('2002-12-07',periods=903,freq='7D').strftime('%Y-%m-%d')
    history['bonus']=[next(n for n in range(1,46) if n not in row) for row in numbers]
    audit=[]
    class TracedGraph(GraphStructureModel):
        def fit(self,past,*,cutoff):audit.append(('fit',len(past),cutoff));return super().fit(past,cutoff=cutoff)
        def score_matrix(self,past,*,target):audit.append(('score',len(past),target-1));return super().score_matrix(past,target=target)
    rows=annotate_cutoffs(walk_forward(history,{'GraphStructureModel':TracedGraph},start=901,end=903,cadence=2,combined=False))
    assert audit==[('fit',900,900),('score',900,900),('score',901,901),('fit',902,902),('score',902,902)]
    g=rows[rows.model=='GraphStructureModel']
    assert g.training_cutoff.tolist()==[900,901,902] and g.outer_fit_cutoff.tolist()==[900,900,902]


def test_paired_report_includes_frequency_reference():
    from src.backtest.graph_hypergraph import paired_report
    from src.backtest.ranking import rank_metrics
    names=['GraphStructureModel','HypergraphModel','RandomModel','Frequency26','GapLogistic','MatchedGraphFrequency','MatchedHypergraphFrequency']
    rows=[]
    for target in (1243,1244,1245):
        for index,name in enumerate(names):
            ranking=np.roll(np.arange(1,46),index).tolist();actual=set(range(1,7))
            rows.append(dict(model=name,target_draw=target,**rank_metrics(ranking,actual),
                **{f'pool_{k}':len(set(ranking[:k])&actual) for k in (6,8,10,12,15)}))
    result=paired_report(pd.DataFrame(rows),replicates=30)
    assert {'RandomModel','Frequency26','GapLogistic'}<=set(result.reference)


def test_factories_support_all_declared_matched_frequency_windows():
    from src.backtest.graph_hypergraph import factories
    x=iid_surrogate(241,seed=84)
    for W in (26,52,104):
        selection=dict(models={
            'GraphStructureModel':dict(model='GraphStructureModel',window=W,feature='neighbor',communities=2),
            'HypergraphModel':dict(model='HypergraphModel',window=W,support=2,shrinkage=10)},consensus_allowed=False)
        models=factories(selection)
        for name,window in [('Frequency26',26),('MatchedGraphFrequency',W),('MatchedHypergraphFrequency',W)]:
            model=models[name]().fit(x[:240],cutoff=240)
            scores=model.score_matrix(x,target=242)
            assert np.allclose(list(scores.values()),x[-window:].mean(0))
            with pytest.raises(ValueError):model.score_matrix(x,target=1246)
