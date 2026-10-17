import copy
import pytest
import socket
from src.freeze_artifacts import digest

def test_phase9_offline_three_tracks_prior_isolation_and_nonoverwrite(history,tmp_path,monkeypatch):
    from test_features import extend
    from src.phase9_freeze import freeze_joint,verify_joint
    source=tmp_path/'history.csv';extend(history,120).to_csv(source,index=False)
    root=tmp_path/'prospective';root.mkdir();protected={}
    for phase in (5,6,7,8):
        d=root/f'phase{phase}';d.mkdir();f=d/'snapshot.json';f.write_text('immutable evidence')
        protected[f.relative_to(root).as_posix()]=digest(f)
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('Network forbidden'))
    paths=freeze_joint(source,root/'phase9',expected_target=121,protected=protected)
    p=verify_joint(paths['snapshot'])
    assert len(p['models'])==3 and p['status']=='FROZEN_UNEVALUATED' and p['target_draw']==121
    assert p['dataset_hash']==digest(source) and not p['future_result_accessed'] and len(p['prior_artifact_hashes'])==4
    for track in p['models'].values():
        assert track['configuration']['window']==26 and track['configuration']['continuous_4d_search'] is False
        assert sorted(track['ranking'])==list(range(1,46))
        for k in (6,8,10,12,15):assert track['top_k'][str(k)]==track['ranking'][:k]
        for group in track['portfolios'].values():assert len(set(map(tuple,group['20'])))==20
    before={f:f.read_bytes() for f in root.rglob('*') if f.is_file()}
    with pytest.raises(ValueError,match='already'):freeze_joint(source,root/'phase9',expected_target=121,protected=protected)
    assert all(f.read_bytes()==b for f,b in before.items())
    from src.phase9_artifacts import publish_joint
    for bad in ('metadata','identity','encoder','baseline','scores'):
        q=copy.deepcopy(p)
        if bad=='metadata':del q['created_at']
        if bad=='identity':q['experiment_id']='draw1246_phase9_joint4dstate_synthetic'
        if bad=='encoder':q['fitted_models']['JointStateTranslationModel']['encoder']['frequency']['training_cutoff']=121
        if bad=='baseline':q['fitted_models']['JointStateFrequencyBaseline']['posterior'][0]=1.
        if bad=='scores':
            from src.freeze_artifacts import prepare_track
            q['models']['JointStateFrequencyBaseline']=prepare_track({n:.99 for n in range(1,46)},
                q['models']['JointStateFrequencyBaseline']['configuration'],seed=42,portfolios=True)
        with pytest.raises(ValueError):publish_joint(q,tmp_path/bad/'phase9',protected={})
        assert not (tmp_path/bad/'phase9').exists()
    paths['manifest'].write_text('tamper')
    with pytest.raises(ValueError,match='integrity'):verify_joint(paths['snapshot'])

def test_phase9_wrong_cutoff_or_namespace_cannot_reserve(history,tmp_path):
    from test_features import extend
    from src.phase9_freeze import freeze_joint
    source=tmp_path/'history.csv';extend(history,120).to_csv(source,index=False)
    with pytest.raises(ValueError):freeze_joint(source,tmp_path/'phase8',expected_target=121,protected={})
    with pytest.raises(ValueError,match='cutoff'):freeze_joint(source,tmp_path/'phase9',expected_target=122,protected={})
    assert not (tmp_path/'phase9').exists()
