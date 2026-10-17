import copy
import socket
import pytest
from src.freeze_artifacts import digest


def test_phase10_three_tracks_are_offline_isolated_immutable_and_consistent(history,tmp_path,monkeypatch):
    from test_features import extend
    from src.phase10_freeze import freeze_number_space
    from src.phase10_artifacts import verify_number_space,publish,validate
    source=tmp_path/'history.csv';extend(history,120).to_csv(source,index=False)
    root=tmp_path/'prospective';root.mkdir();protected={}
    for phase in (5,6,7,8,9):
        p=root/f'phase{phase}';p.mkdir();f=p/'old.json';f.write_text('immutable evidence')
        protected[f.relative_to(root).as_posix()]=digest(f)
    selection=dict(version='phase10-development-v1',development_start=106,development_end=110,later_start=111,
        range=dict(window=26,width=5),neighborhood=dict(window=26,kernel='triangular1'),gap_weight=.5)
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('Network forbidden'))
    paths=freeze_number_space(source,root/'phase10',expected_target=121,protected=protected,selection=selection)
    p=verify_number_space(paths['snapshot'])
    assert p['target_draw']==121 and p['training_cutoff']==120 and p['status']=='FROZEN_UNEVALUATED'
    assert len(p['models'])==3 and len(p['prior_artifact_hashes'])==5
    for track in p['models'].values():
        assert set(track['ranking'])==set(range(1,46))
        for k in (6,8,10,12,15):assert track['top_k'][str(k)]==track['ranking'][:k]
        for group in track['portfolios'].values():assert len(set(map(tuple,group['20'])))==20
    before={q:q.read_bytes() for q in root.rglob('*') if q.is_file()}
    with pytest.raises(ValueError,match='already'):freeze_number_space(source,root/'phase10',expected_target=121,protected=protected,selection=selection)
    assert all(q.read_bytes()==value for q,value in before.items())
    for field in ('selection','scores','cutoff','kernel','source'):
        q=copy.deepcopy(p)
        if field=='selection':q['selection']['development_end']=121
        if field=='scores':q['models']['NeighborhoodModel']['scores']={n:.99 for n in range(1,46)}
        if field=='cutoff':q['fitted']['gap']['training_cutoff']=121
        if field=='kernel':q['models']['NeighborhoodModel']['configuration']['kernel']='none'
        if field=='source':q['sources']['bad']='not matching the source archive'
        with pytest.raises(ValueError):publish(q,tmp_path/field/'phase10',protected={})
        assert not (tmp_path/field/'phase10').exists()
    paths['manifest'].write_text('tampered')
    with pytest.raises(ValueError,match='integrity'):verify_number_space(paths['snapshot'])


def test_phase10_rejects_wrong_namespace_and_cutoff_before_reservation(history,tmp_path):
    from test_features import extend
    from src.phase10_freeze import freeze_number_space
    source=tmp_path/'history.csv';extend(history,120).to_csv(source,index=False)
    with pytest.raises(ValueError):freeze_number_space(source,tmp_path/'phase9',expected_target=121,protected={})
    with pytest.raises(ValueError):freeze_number_space(source,tmp_path/'phase10',expected_target=122,protected={})
    assert not (tmp_path/'phase10').exists()


def test_real_historical_evidence_must_bind_to_the_same_dataset():
    import pandas as pd
    from hashlib import sha256
    from src.phase10_freeze import validate_historical_provenance
    from src.backtest.number_space import configuration_hash
    # Synthetic identifiers only, not actual draw outcomes.
    data=pd.DataFrame(dict(draw_no=range(1,1246)))
    selected=dict(development_start=401,development_end=900,later_start=901,
        development_data_hash=sha256(data.iloc[:900].to_csv(index=False).encode()).hexdigest())
    full=sha256(data.to_csv(index=False).encode()).hexdigest();canonical='a'*64
    analysis=dict(cutoff=1245,dataset_hash=canonical)
    protocols=[dict(start=401,end=1245,development_end=900,later_start=901,selected_configuration_hash=configuration_hash(selected),input_data_hash=full) for _ in (26,13)]
    validate_historical_provenance(data,canonical,selected,analysis,protocols)
    for which in ('development','analysis','evaluation'):
        s=copy.deepcopy(selected);a=copy.deepcopy(analysis);p=copy.deepcopy(protocols)
        if which=='development':s['development_data_hash']='b'*64
        if which=='analysis':a['dataset_hash']='b'*64
        if which=='evaluation':p[1]['input_data_hash']='b'*64
        with pytest.raises(ValueError):validate_historical_provenance(data,canonical,s,a,p)
