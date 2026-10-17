import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.backtest.transformed_space import candidates,select_development,configuration_hash,load_selection,paired_report,rank_diversity
from src.phase15_freeze import prepare_freeze,PENDING


def test_development_only_selection_and_space():
    specs=candidates();assert len(specs)==60
    rows=pd.DataFrame([dict(candidate=c,target_draw=t,hits=h) for c,h in [('a',1),('b',2)] for t in (899,900)])
    assert select_development(rows)=='b'
    with pytest.raises(ValueError):select_development(rows.assign(target_draw=[899,900,900,901]))
    with pytest.raises(ValueError):select_development(rows.iloc[:-1])


def test_hash_and_configuration_validation(tmp_path):
    s=dict(version='phase15-v1',research_cutoff=1245,development_end=900,later_start=901,candidate_count=60,
        models={'ModularResidueModel':dict(model='ModularResidueModel',modulus=2,lag=1),
                'DifferenceRelationModel':dict(model='DifferenceRelationModel',lag=1,support=20)},shape_allowed=False,consensus_allowed=False)
    p=tmp_path/'selection.json';p.write_text(json.dumps(dict(selection=s,sha256=configuration_hash(s))))
    assert load_selection(p)==s
    s['models']['ModularResidueModel']['modulus']=8
    p.write_text(json.dumps(dict(selection=s,sha256=configuration_hash(s))))
    with pytest.raises(ValueError):load_selection(p)


def test_future_suffix_and_publication_block(tmp_path):
    from src.transformed_cli import load_research_source,guard
    source=tmp_path/'future.csv';source.write_bytes(Path('data/raw/lotto_history.csv').read_bytes()+b'1246,UNREADABLE_FUTURE\xff\n')
    with pytest.raises(ValueError,match='unknown suffix'):load_research_source(source)
    with pytest.raises(ValueError):guard('reports/prospective')
    with pytest.raises(ValueError,match=PENDING):prepare_freeze(tmp_path/'none',tmp_path/'absent')
    with pytest.raises(ValueError):prepare_freeze(tmp_path/'none',tmp_path/'absent',target=1246)
    assert not (tmp_path/'absent').exists()


def test_rank_coordinates_and_paired_references():
    from src.backtest.ranking import rank_metrics
    a=list(range(1,46));assert rank_diversity(a,a)['spearman']==pytest.approx(1)
    assert rank_diversity(a,a[::-1])['spearman']==pytest.approx(-1)
    rows=[]
    for target in (1243,1244,1245):
        for i,name in enumerate(('ModularResidueModel','DifferenceRelationModel','RandomModel','GapLogistic','Frequency26')):
            ranking=np.roll(a,i).tolist();actual=set(range(1,7))
            rows.append(dict(model=name,target_draw=target,**rank_metrics(ranking,actual),
                **{f'pool_{k}':len(set(ranking[:k])&actual) for k in (6,8,10,12,15)}))
    r=paired_report(pd.DataFrame(rows),replicates=30)
    assert set(r.reference)=={'RandomModel','GapLogistic'}


def test_walk_forward_actual_training_prefixes():
    from src.backtest.translation import walk_forward
    from src.backtest.transformed_space import annotate_cutoffs
    from src.models.transformed_space import ModularResidueModel
    from src.collect.dataset import MAIN_COLUMNS
    x=iid_surrogate(903,seed=157);numbers=np.array([np.flatnonzero(row)+1 for row in x])
    history=pd.DataFrame(numbers,columns=MAIN_COLUMNS);history['draw_no']=np.arange(1,904)
    history['draw_date']=pd.date_range('2002-12-07',periods=903,freq='7D').strftime('%Y-%m-%d')
    history['bonus']=[next(n for n in range(1,46) if n not in row) for row in numbers];audit=[]
    class Trace(ModularResidueModel):
        def fit(self,past,*,cutoff):audit.append(('fit',len(past),cutoff));return super().fit(past,cutoff=cutoff)
        def score_matrix(self,past,*,target):audit.append(('score',len(past),target-1));return super().score_matrix(past,target=target)
    r=annotate_cutoffs(walk_forward(history,{'ModularResidueModel':Trace},start=901,end=903,cadence=2,combined=False))
    assert audit==[('fit',900,900),('score',900,900),('score',901,901),('fit',902,902),('score',902,902)]
    g=r[r.model=='ModularResidueModel'];assert g.training_cutoff.tolist()==[900,901,902]
    assert g.outer_fit_cutoff.tolist()==[900,900,902]
