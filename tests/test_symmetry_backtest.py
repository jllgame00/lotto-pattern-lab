"""Causal H16 selection, paired references and frozen-output integrity."""
import json
from hashlib import sha256
import numpy as np
import pandas as pd
import pytest
from src.backtest import symmetry as bt
from src.backtest.ranking import rank_metrics
from src.analysis.spatiotemporal import iid_surrogate


def selection(x):
    name, config = next(iter(bt.candidates().items()))
    return dict(version='phase18-v1', research_cutoff=1245, development_start=401,
        development_end=900, later_start=901, candidate_count=48,
        models={'MirrorModel': config}, selected_candidates={'MirrorModel': name},
        pair_model_allowed=False, support=20, selection_metric='meanTop6hits;tiesdeclaredorder',
        development_matrix_hash=sha256(x[:900].tobytes()).hexdigest(), draw1246_used=False)


def test_selection_rejects_future_duplicates_and_mismatched_targets():
    rows=pd.DataFrame([dict(candidate=c,target_draw=t,hits=h) for c,h in [('a',1),('b',2)] for t in (899,900)])
    assert bt.select_development(rows)=='b'
    for broken in (rows.assign(target_draw=[899,900,900,901]), rows.iloc[:-1], pd.concat([rows,rows.iloc[:1]])):
        with pytest.raises(ValueError):bt.select_development(broken)
    with pytest.raises(ValueError):bt.select_development(rows.assign(target_draw=901),end=901)


def test_declared_ties_and_frozen_selection_integrity(tmp_path):
    specs=bt.candidates(); assert len(specs)==48
    keys=list(specs)
    rows=pd.DataFrame([dict(candidate=c,target_draw=900,hits=1) for c in keys[::-1]])
    assert bt.select_development(rows)==keys[0]
    s=selection(iid_surrogate(900,seed=18)); path=tmp_path/'selection.json'
    path.write_text(json.dumps(dict(selection=s,sha256=bt.configuration_hash(s))))
    assert bt.load_selection(path)==s
    for key,value in [('pair_model_allowed',True),('later_start',902),('support',19)]:
        bad=dict(s);bad[key]=value
        path.write_text(json.dumps(dict(selection=bad,sha256=bt.configuration_hash(bad))))
        with pytest.raises(ValueError):bt.load_selection(path)
    path.write_text(json.dumps(dict(selection=s,sha256='0'*64)))
    with pytest.raises(ValueError):bt.load_selection(path)


def test_development_scores_only_completed_prefix_and_fixed_control(monkeypatch):
    x=iid_surrogate(900,seed=18)
    class PrefixModel:
        def fit(self,past,*,cutoff):
            assert cutoff==len(past)<900
            self.prefix=past.copy();return self
        def score_matrix(self,past,*,target):
            assert target==len(past)+1 and np.array_equal(past,self.prefix)
            return dict(enumerate(past[-1].astype(float),1))
    monkeypatch.setattr(bt,'construct',lambda config:PrefixModel())
    s,rows=bt.development_search(x)
    assert len(rows)==24500 and set(rows.target_draw)==set(range(401,901))
    assert s['models']=={'MirrorModel':next(iter(bt.candidates().values()))}
    control=rows[(rows.candidate=='frequency26') & (rows.target_draw==401)].iloc[0]
    # Independently sort frequencies with ascending number as tie breaker.
    top=sorted(range(45),key=lambda i:(-x[374:400,i].sum(),i))[:6]
    assert control.hits==int(x[400,top].sum())
    with pytest.raises(ValueError):bt.development_search(x[:-1])


def ranking_rows(targets=(901,902,903)):
    result=[];actual=list(range(1,7))
    for t in targets:
        for i,name in enumerate(('MirrorModel','RandomModel','Frequency26','GapLogistic')):
            rank=np.roll(np.arange(1,46),i).tolist()
            result.append(dict(model=name,target_draw=t,training_cutoff=900,feature_cutoff=t-1,
                ranking=json.dumps(rank),actual=json.dumps(actual),**rank_metrics(rank,actual),
                **{f'pool_{k}':len(set(rank[:k])&set(actual)) for k in (6,8,10,12,15)}))
    return pd.DataFrame(result)


def test_paired_frequency_reference_and_target_matching():
    rows=ranking_rows()
    result=bt.paired_report(rows,replicates=20,block=26)
    assert set(result.reference)=={'RandomModel','Frequency26','GapLogistic'}
    assert len(result)==45
    delta=result[(result.reference=='Frequency26') & (result.metric=='hits')].iloc[0]
    assert delta.difference==2 and delta.ci_low==2 and delta.ci_high==2
    for broken in (rows.iloc[:-1],pd.concat([rows,rows.iloc[:1]])):
        with pytest.raises(ValueError):bt.paired_report(broken,replicates=20)


def test_diversity_uses_number_rank_coordinates_and_matches_frozen_actuals(tmp_path):
    rows=ranking_rows();path=tmp_path/'graph.csv'
    old=rows[rows.model=='GapLogistic'].copy();old['model']='GraphStructureModel'
    old.to_csv(path,index=False)
    report=bt.correlation_report(rows,graph_path=path)
    assert set(report.reference)=={'GapLogistic','Phase14Graph'}
    a=json.loads(rows.iloc[0].ranking); b=json.loads(old.iloc[0].ranking)
    # Independently compute Spearman on the rank assigned to each NUMBER.
    ar=np.array([a.index(n) for n in range(1,46)]);br=np.array([b.index(n) for n in range(1,46)])
    assert report.iloc[0].spearman==pytest.approx(1-6*np.square(ar-br).sum()/(45*(45**2-1)))
    old.loc[old.index[0],'actual']=json.dumps([2,3,4,5,6,7]);old.to_csv(path,index=False)
    with pytest.raises(ValueError):bt.correlation_report(rows,graph_path=path)


def frozen_archive(tmp_path,x):
    directory=tmp_path/'frozen';directory.mkdir();output=directory/'walk_forward_26';output.mkdir()
    rows=[]
    for target in range(901,1246):
        actual=(np.flatnonzero(x[target-1])+1).tolist();rank=list(range(1,46))
        rows.append(dict(model='GapLogistic',target_draw=target,training_cutoff=900+(target-901)//26*26,
            feature_cutoff=target-1,ranking=json.dumps(rank),actual=json.dumps(actual),**rank_metrics(rank,actual),
            **{f'pool_{k}':len(set(rank[:k])&set(actual)) for k in (6,8,10,12,15)}))
    path=output/'predictions.csv';pd.DataFrame(rows).to_csv(path,index=False)
    metadata=directory/'analysis_metadata.json';metadata.write_text(json.dumps(dict(matrix_hash=sha256(x.tobytes()).hexdigest())))
    manifest=dict(research_cutoff=1245,draw1246_used=False,artifacts={})
    for p in (path,metadata):manifest['artifacts'][p.relative_to(directory).as_posix()]={'sha256':sha256(p.read_bytes()).hexdigest()}
    (directory/'run_manifest.json').write_text(json.dumps(manifest))
    return directory,path


def test_frozen_gap_requires_manifest_and_current_source_integrity(tmp_path,monkeypatch):
    x=iid_surrogate(1245,seed=18);directory,path=frozen_archive(tmp_path,x)
    monkeypatch.setattr(bt,'FROZEN_DIRECTORY',directory)
    rows=bt.frozen_gap(x[:903],cadence=26)
    assert rows.target_draw.tolist()==[901,902,903]
    changed=x[:903].copy();changed[0]=x[1]
    with pytest.raises(ValueError):bt.frozen_gap(changed,cadence=26)
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='hash|integrity'):bt.frozen_gap(x[:903],cadence=26)


def test_effective_and_outer_fit_cutoffs_are_separate():
    rows=bt.annotate_cutoffs(ranking_rows())
    for name in ('MirrorModel','Frequency26'):
        here=rows[rows.model==name]
        assert here.training_cutoff.tolist()==[900,901,902]
        assert here.outer_fit_cutoff.tolist()==[900,900,900]
    assert rows[rows.model=='GapLogistic'].training_cutoff.tolist()==[900,900,900]


def test_evaluate_uses_causal_prefixes_and_frozen_gap_without_old_fits(tmp_path,monkeypatch):
    from src.collect.dataset import MAIN_COLUMNS
    x=iid_surrogate(1245,seed=18);directory,_=frozen_archive(tmp_path,x)
    monkeypatch.setattr(bt,'FROZEN_DIRECTORY',directory)
    class PrefixModel:
        def fit(self,past,*,cutoff):
            assert len(past)==cutoff
            self.training=past.copy();self.training_cutoff=cutoff;return self
        def score_matrix(self,past,*,target):
            assert target==len(past)+1 and np.array_equal(past[:self.training_cutoff],self.training)
            return dict(enumerate(past[-1].astype(float),1))
    monkeypatch.setattr(bt,'construct',lambda config:PrefixModel())
    numbers=np.array([np.flatnonzero(row)+1 for row in x[:903]])
    history=pd.DataFrame(numbers,columns=MAIN_COLUMNS);history['draw_no']=np.arange(1,904)
    history['draw_date']=pd.date_range('2002-12-07',periods=903,freq='7D').strftime('%Y-%m-%d')
    history['bonus']=[next(n for n in range(1,46) if n not in row) for row in numbers]
    result=bt.evaluate(history,selection(x),cadence=26)
    assert len(result)==12 and set(result.model)=={'MirrorModel','Frequency26','RandomModel','GapLogistic'}
    mirror=result[result.model=='MirrorModel']
    assert mirror.training_cutoff.tolist()==[900,901,902]
    assert mirror.outer_fit_cutoff.tolist()==[900,900,900]
    assert result[result.model=='GapLogistic'].ranking.tolist()==[json.dumps(list(range(1,46)))]*3
    invalid=selection(x);invalid['development_matrix_hash']='0'*64
    with pytest.raises(ValueError,match='prefix'):bt.evaluate(history,invalid)


def test_frozen_rejects_bad_ranking_even_with_updated_file_digest(tmp_path,monkeypatch):
    x=iid_surrogate(1245,seed=18);directory,path=frozen_archive(tmp_path,x)
    monkeypatch.setattr(bt,'FROZEN_DIRECTORY',directory)
    rows=pd.read_csv(path);rows.loc[0,'ranking']=json.dumps([1]*45);rows.to_csv(path,index=False)
    manifest_path=directory/'run_manifest.json';manifest=json.loads(manifest_path.read_text())
    manifest['artifacts']['walk_forward_26/predictions.csv']['sha256']=sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='ranking'):bt.frozen_gap(x[:903])


def test_diversity_is_not_correlation_of_number_order():
    rows=ranking_rows((901,));rank=np.random.default_rng(194).permutation(np.arange(1,46)).tolist()
    mask=rows.model=='MirrorModel'
    rows.loc[mask,'ranking']=json.dumps(rank)
    for key,value in rank_metrics(rank,set(range(1,7))).items():rows.loc[mask,key]=value
    for k in (6,8,10,12,15):rows.loc[mask,f'pool_{k}']=len(set(rank[:k])&set(range(1,7)))
    reference=json.loads(rows[rows.model=='GapLogistic'].iloc[0].ranking)
    coordinates=np.array([rank.index(i)-reference.index(i) for i in range(1,46)])
    expected=1-6*np.square(coordinates).sum()/(45*(45**2-1))
    assert bt.correlation_report(rows).iloc[0].spearman==pytest.approx(expected)


def test_selection_grid_rejects_boolean_lag(tmp_path):
    s=selection(iid_surrogate(900,seed=18))
    s['models']['MirrorModel']['lag']=True
    path=tmp_path/'selection.json';path.write_text(json.dumps(dict(selection=s,sha256=bt.configuration_hash(s))))
    with pytest.raises(ValueError):bt.load_selection(path)
