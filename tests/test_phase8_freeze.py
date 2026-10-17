import json
import socket
import pytest
from src.freeze_artifacts import digest

def test_offline_phase8_isolation_contents_and_nonoverwrite(history,tmp_path,monkeypatch):
    from test_features import extend
    from src.phase8_freeze import freeze_frequency,verify_frequency
    data=extend(history,120);source=tmp_path/'history.csv';data.to_csv(source,index=False)
    root=tmp_path/'prospective';root.mkdir();protected={}
    for phase in (5,6,7):
        d=root/f'phase{phase}';d.mkdir();f=d/'snapshot.json';f.write_text('original frozen evidence')
        protected[f.relative_to(root).as_posix()]=digest(f)
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('Network forbidden'))
    paths=freeze_frequency(source,root/'phase8',expected_target=121,protected=protected)
    p=verify_frequency(paths['snapshot'])
    assert p['status']=='FROZEN_UNEVALUATED' and p['target_draw']==121 and p['training_cutoff']==120
    assert not p['future_result_accessed'] and p['dataset_hash']==digest(source)
    assert len(p['prior_artifact_hashes'])==3 and p['sources'] and p['source_hashes']
    for track in p['models'].values():
        assert track['configuration']['window']==26 and not track['configuration']['gap_features_used']
        assert sorted(track['ranking'])==list(range(1,46))
        for k in (6,8,10,12,15): assert track['top_k'][str(k)]==track['ranking'][:k]
        for group in track['portfolios'].values():
            assert len(set(map(tuple,group['20'])))==20
            assert all(len(group[str(k)])==k for k in (1,5,10,20))
    before={f:f.read_bytes() for f in root.rglob('*') if f.is_file()}
    with pytest.raises(ValueError,match='already'): freeze_frequency(source,root/'phase8',expected_target=121,protected=protected)
    assert all(f.read_bytes()==b for f,b in before.items())
    paths['manifest'].write_text('tamper')
    with pytest.raises(ValueError,match='integrity'): verify_frequency(paths['snapshot'])

def test_wrong_scope_cannot_create_phase8_reservation(history,tmp_path):
    from test_features import extend
    from src.phase8_freeze import freeze_frequency
    source=tmp_path/'history.csv';extend(history,120).to_csv(source,index=False)
    with pytest.raises(ValueError): freeze_frequency(source,tmp_path/'phase7',expected_target=121,protected={})
    with pytest.raises(ValueError,match='cutoff'): freeze_frequency(source,tmp_path/'phase8',expected_target=122,protected={})
    assert not (tmp_path/'phase8').exists()

def test_bad_payload_rejected_before_reservation(tmp_path):
    from src.phase8_freeze import publish_frequency
    with pytest.raises(ValueError): publish_frequency({'phase':8},tmp_path/'phase8',protected={})
    assert not (tmp_path/'phase8').exists()

def synthetic_payload():
    from src.analysis.spatiotemporal import iid_surrogate
    from src.models.frequency3d import FrequencyConditionedTranslationModel,FrequencyConditionedChainModel
    from src.freeze_artifacts import prepare_track
    models={cls.__name__:cls().fit(iid_surrogate(120,seed=8),cutoff=120) for cls in
            (FrequencyConditionedTranslationModel,FrequencyConditionedChainModel)}
    return dict(schema_version='phase8-frequency3d-v1',phase=8,experiment_id='draw121_phase8_frequency3d_synthetic',
        target_draw=121,training_cutoff=120,status='FROZEN_UNEVALUATED',future_result_accessed=False,seed=42,
        created_at='2026-10-17T00:00:00+09:00',latest_training_date='2005-03-19',git_sha='synthetic',
        git_dirty=True,dataset_hash='a'*64,feature_version='pre-draw-frequency-v1',environment={'synthetic':True},
        models={n:prepare_track({i:i/45 for i in range(1,46)},m.configuration(),seed=42,portfolios=True) for n,m in models.items()},
        fitted_models={n:dict(training_cutoff=120,configuration=m.configuration(),encoder=m.encoder.configuration(),rules=m.rules) for n,m in models.items()})

@pytest.mark.parametrize('mutation',['metadata','identity','target_type','window','encoder','nonfinite'])
def test_invalid_metadata_and_configs_cannot_reserve(tmp_path,mutation):
    from src.phase8_artifacts import publish_frequency
    p=synthetic_payload()
    if mutation=='metadata': del p['created_at']
    if mutation=='identity': p['experiment_id']='draw1246_phase8_frequency3d_synthetic'
    if mutation=='target_type': p['target_draw']=121.0
    if mutation=='window': p['models']['FrequencyConditionedChainModel']['configuration']['window']=52
    if mutation=='encoder': del p['fitted_models']['FrequencyConditionedChainModel']['encoder']['quantile_edges']
    if mutation=='nonfinite': p['environment']['bad']=float('nan')
    with pytest.raises(ValueError): publish_frequency(p,tmp_path/'phase8',protected={})
    assert not (tmp_path/'phase8').exists()

def test_verification_uses_frozen_contract_not_later_defaults(tmp_path,monkeypatch):
    from src.phase8_artifacts import publish_frequency,verify_frequency
    from src.models.frequency3d import FrequencyConditionedTranslationModel
    paths=publish_frequency(synthetic_payload(),tmp_path/'phase8',protected={})
    monkeypatch.setattr(FrequencyConditionedTranslationModel,'configuration',lambda self:{'future_version':99})
    assert verify_frequency(paths['snapshot'])['status']=='FROZEN_UNEVALUATED'
