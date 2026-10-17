import json
import numpy as np
import pandas as pd
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.models.multiscale import WaveletPhaseModel,SSAModel
from src.backtest.multiscale import select_development,rank_diversity,configuration_hash
from src.phase12_freeze import prepare_freeze,PENDING


@pytest.mark.parametrize('cls',[WaveletPhaseModel,SSAModel])
def test_model_training_only_component_selection(cls):
    x=iid_surrogate(240,seed=1)
    m=cls().fit(x,cutoff=240)
    a=m.score_matrix(x,target=241)
    assert set(a)==set(range(1,46)) and np.isfinite(list(a.values())).all()
    assert a==cls().fit(x.copy(),cutoff=240).score_matrix(x.copy(),target=241)
    changed=x.copy();changed[0]=iid_surrogate(2,seed=3)[0]
    with pytest.raises(ValueError): m.score_matrix(changed,target=241)
    with pytest.raises(ValueError): m.fit(x,cutoff=239)
    with pytest.raises(ValueError): m.score_matrix(x,target=242)
    with pytest.raises(ValueError): m.score_matrix(iid_surrogate(1245,seed=2),target=1246)
    with pytest.raises(ValueError): cls().fit(iid_surrogate(1246,seed=2),cutoff=1246)


def test_development_only_selection_and_target_parity():
    rows=pd.DataFrame([dict(candidate=c,target_draw=t,hits=h) for c,h in [('a',1),('b',2)] for t in (899,900)])
    assert select_development(rows)=='b'
    with pytest.raises(ValueError): select_development(pd.concat([rows,pd.DataFrame([dict(candidate='a',target_draw=901,hits=6)])]))
    with pytest.raises(ValueError): select_development(rows.iloc[:-1])
    assert configuration_hash({'a':1,'b':2})==configuration_hash({'b':2,'a':1})


def test_rank_correlation_aligns_numbers():
    a=list(range(1,46)); b=a[::-1]
    assert rank_diversity(a,a)['spearman']==pytest.approx(1)
    assert rank_diversity(a,b)['spearman']==pytest.approx(-1)
    assert rank_diversity(a,b)['top6_overlap']==0


def test_archive_missing_blocks_draw1247_without_publication(tmp_path):
    p=tmp_path/'selected.json';p.write_text('{}')
    with pytest.raises(ValueError,match=PENDING):prepare_freeze(p,tmp_path/'absent')
    with pytest.raises(ValueError):prepare_freeze(p,tmp_path/'absent',target=1246)
    assert list(tmp_path.iterdir())==[p]


def test_walk_forward_fits_before_each_target_and_rejects_future():
    from src.backtest.translation import walk_forward
    from src.collect.dataset import MAIN_COLUMNS
    x=iid_surrogate(243,seed=25)
    numbers=np.array([np.flatnonzero(row)+1 for row in x])
    history=pd.DataFrame(numbers,columns=MAIN_COLUMNS)
    history['draw_no']=np.arange(1,244)
    history['draw_date']=pd.date_range('2002-12-07',periods=243,freq='7D').strftime('%Y-%m-%d')
    history['bonus']=[next(n for n in range(1,46) if n not in row) for row in numbers]
    audits=[]
    class AuditedSSA(SSAModel):
        def fit(self,past,*,cutoff):
            audits.append(('fit',cutoff,len(past)));return super().fit(past,cutoff=cutoff)
        def score_matrix(self,past,*,target):
            audits.append(('score',target-1,len(past)));return super().score_matrix(past,target=target)
    rows=walk_forward(history,{'SSAModel':AuditedSSA},start=241,end=243,cadence=2,combined=False)
    assert audits==[('fit',240,240),('score',240,240),('score',241,241),('fit',242,242),('score',242,242)]
    assert (rows.feature_cutoff==rows.target_draw-1).all()
    assert (rows.training_cutoff<rows.target_draw).all()
    with pytest.raises(ValueError):walk_forward(history,{},start=241,end=1246)


def test_no_phase12_parse_of_draw1246_suffix(tmp_path):
    from src.recurrence_cli import load_research_source
    from pathlib import Path
    original=Path('data/raw/lotto_history.csv').read_bytes()
    path=tmp_path/'suffix.csv';path.write_bytes(original+b'1246,UNREADABLE_FUTURE_SUFFIX\xff\n')
    with pytest.raises(ValueError,match='unknown suffix'):load_research_source(path)


def test_cli_phase12_and_output_path_guard():
    from src.cli import _parser
    from src.multiscale_cli import guard
    args=_parser().parse_args(['multiscale','prepare-freeze'])
    assert args.action=='prepare-freeze'
    with pytest.raises(ValueError):guard('reports/prospective')


def test_frozen_selection_rejects_mutation(tmp_path):
    from src.backtest.multiscale import load_selection,candidates
    s=dict(research_cutoff=1245,development_end=900,later_start=901,candidate_count=12,
        models={'WaveletPhaseModel':candidates()['wavelet_s0_c2'],'SSAModel':candidates()['ssa_L26_leading2']})
    p=tmp_path/'selection.json';p.write_text(json.dumps(dict(selection=s,sha256=configuration_hash(s))))
    assert load_selection(p)==s
    s['models']['SSAModel']['length']=156
    p.write_text(json.dumps(dict(selection=s,sha256=configuration_hash(s))))
    with pytest.raises(ValueError):load_selection(p)


def test_invalid_analysis_options_leave_no_artifacts(tmp_path):
    from src.multiscale_cli import analyze
    for replicates,workers in [(0,1),(1,0)]:
        with pytest.raises(ValueError):analyze(iid_surrogate(1245,seed=2),tmp_path,replicates,workers)
        assert list(tmp_path.iterdir())==[]


def test_actual_decompositions_use_target_training_prefix(monkeypatch):
    import src.models.multiscale as module
    x=iid_surrogate(1245,seed=76)
    original_wavelet=module.morlet_transform;original_ssa=module.decompose
    wavelet_inputs=[];ssa_inputs=[]
    def traced_wavelet(values,**kwargs):
        wavelet_inputs.append(values.copy());return original_wavelet(values,**kwargs)
    def traced_ssa(values,*args,**kwargs):
        ssa_inputs.append(values.copy());return original_ssa(values,*args,**kwargs)
    monkeypatch.setattr(module,'morlet_transform',traced_wavelet)
    monkeypatch.setattr(module,'decompose',traced_ssa)
    for target in (901,1245):
        module._transform.cache_clear();module._ssa_both.cache_clear()
        wavelet_inputs.clear();ssa_inputs.clear()
        for cls in (WaveletPhaseModel,SSAModel):
            model=cls().fit(x[:900],cutoff=900)
            model.score_matrix(x[:target-1],target=target)
            with pytest.raises(ValueError):model.score_matrix(x,target=target)
        expected=x[max(0,target-1-416):target-1]
        assert len(wavelet_inputs)==1 and np.array_equal(wavelet_inputs[0],expected)
        assert len(ssa_inputs)==45
        assert np.array_equal(np.column_stack(ssa_inputs),expected)
