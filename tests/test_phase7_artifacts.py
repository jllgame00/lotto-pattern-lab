import json
from pathlib import Path
from hashlib import sha256
import pytest
from src.freeze_artifacts import prepare_track,digest


def payload():
    from src.models import gap3d
    from src.analysis.spatiotemporal import iid_surrogate
    names=('GapConditionedTranslationModel','GapConditionedChainModel')
    fitted={name:getattr(gap3d,name)().fit(iid_surrogate(120,seed=8),cutoff=120) for name in names}
    models={name:prepare_track({n:n/45 for n in range(1,46)},fitted[name].configuration(),seed=42,portfolios=True) for name in names}
    return dict(schema_version='phase7-gap3d-v1',phase=7,experiment_id='draw121_phase7_gap3d_synthetic',
        target_draw=121,training_cutoff=120,created_at='2026-10-17T00:00:00+09:00',git_sha='synthetic',
        dataset_hash='a'*64,status='FROZEN_UNEVALUATED',future_result_accessed=False,seed=42,
        models=models,environment={'synthetic':True},latest_training_date='2005-03-19',
        git_dirty=True,feature_version='pre-draw-gap-v1',fitted_models={n:dict(training_cutoff=120,
            configuration=m.configuration(),encoder=m.encoder.configuration(),rules=m.rules) for n,m in fitted.items()})


def test_phase7_separate_immutable_artifacts_and_integrity(tmp_path,monkeypatch):
    from src.phase7_artifacts import publish_gap3d,verify_gap3d
    root=tmp_path/'prospective'; root.mkdir(); (root/'phase6').mkdir()
    old=root/'phase5.json'; old.write_bytes(b'original Phase5')
    old6=root/'phase6'/'frozen.json'; old6.write_bytes(b'original Phase6')
    protected={str(p.relative_to(root)):digest(p) for p in (old,old6)}
    import socket
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('Network forbidden'))
    result=publish_gap3d(payload(),root/'phase7',protected=protected)
    value=verify_gap3d(result['snapshot'])
    assert value['target_draw']==121 and value['status']=='FROZEN_UNEVALUATED' and not value['future_result_accessed']
    assert value['prior_artifact_hashes']==protected
    before={p:p.read_bytes() for p in result.values()}
    with pytest.raises(ValueError,match='already'): publish_gap3d(payload(),root/'phase7',protected=protected)
    assert all(p.read_bytes()==b for p,b in before.items())
    assert digest(old)==protected[str(old.relative_to(root))] and digest(old6)==protected[str(old6.relative_to(root))]
    registry=(root/'phase7'/'registry.csv').read_text(); assert digest(result['snapshot']) in registry
    result['manifest'].write_text('tamper')
    with pytest.raises(ValueError,match='integrity'): verify_gap3d(result['snapshot'])


def test_phase7_rejects_wrong_cutoff_and_namespace(tmp_path):
    from src.phase7_artifacts import publish_gap3d
    p=payload(); p['target_draw']=122
    with pytest.raises(ValueError): publish_gap3d(p,tmp_path/'phase7',protected={})
    with pytest.raises(ValueError): publish_gap3d(payload(),tmp_path/'phase6',protected={})


def test_phase7_never_accepts_destination_predictor(tmp_path):
    from src.phase7_artifacts import publish_gap3d
    p=payload(); p['models']['GapConditionedTranslationModel']['configuration']['destination_state_used']=True
    with pytest.raises(ValueError): publish_gap3d(p,tmp_path/'phase7',protected={})


@pytest.mark.parametrize('mutation',['missing_metadata','wrong_identity','missing_rules','nonfinite'])
def test_invalid_payload_cannot_reserve_experiment(tmp_path,mutation):
    from src.phase7_artifacts import publish_gap3d
    p=payload()
    if mutation=='missing_metadata': del p['created_at']
    if mutation=='wrong_identity': p['experiment_id']='draw1246_phase7_gap3d_synthetic'
    if mutation=='missing_rules': del p['fitted_models']['GapConditionedChainModel']['rules']
    if mutation=='nonfinite': p['environment']['bad']=float('nan')
    with pytest.raises(ValueError): publish_gap3d(p,tmp_path/'phase7',protected={})
    assert not (tmp_path/'phase7').exists()


def test_verification_independent_of_future_model_defaults(tmp_path,monkeypatch):
    from src.phase7_artifacts import publish_gap3d,verify_gap3d
    from src.models.gap3d import GapConditionedTranslationModel
    paths=publish_gap3d(payload(),tmp_path/'phase7',protected={})
    monkeypatch.setattr(GapConditionedTranslationModel,'configuration',lambda self:{'future_version':99})
    assert verify_gap3d(paths['snapshot'])['status']=='FROZEN_UNEVALUATED'
