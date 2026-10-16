import json
import socket
from pathlib import Path
import pytest
from test_features import extend
from src.prospective_experiment import freeze_experiment, load_existing_ensemble, strict_source
from src.freeze_artifacts import verify_freeze


COMPONENTS=['GapLogistic','GapHazard','BayesianStatic','BayesianRecent','HMM2','HMM3',
            'SimilarityModel','Frequency52','GapPeriodicityLogistic']


def weights(tmp_path):
    path=tmp_path/'weights.json'
    path.write_text(json.dumps({'Ensemble[DevelopmentWeights]':dict(components=COMPONENTS,
        normalization='rank',weights=[.2]+[.1]*8,development_end=200,selection=[])}))
    return path


def test_complete_synthetic_freeze_uses_existing_models(history,tmp_path,monkeypatch):
    monkeypatch.setattr(socket.socket,'connect',lambda *a,**k:pytest.fail('network forbidden'))
    source=tmp_path/'source.csv'; extend(history,210).to_csv(source,index=False)
    before=source.read_bytes(); w=weights(tmp_path)
    paths=freeze_experiment(source,tmp_path/'prospective',ensemble_path=w,expected_target=211)
    p=verify_freeze(paths['snapshot'])
    assert p['target_draw']==211 and p['training_cutoff']==210
    assert p['status']=='FROZEN_UNEVALUATED'
    assert p['ensemble_source']['configuration']['weights']==[.2]+[.1]*8
    assert p['models']['BayesianStatic']['configuration']['alpha']==2
    assert p['models']['HMM2']['configuration']['states']==2
    assert p['models']['HMM3']['configuration']['states']==3
    assert p['feature_audit']['training_target_max']==210
    assert all(r['feature_cutoff']==210 and r['target_draw']==211 for r in p['current_features'])
    assert all('appeared_next' not in r for r in p['current_features'])
    assert source.read_bytes()==before
    with pytest.raises(ValueError,match='already frozen|reserved'):
        freeze_experiment(source,tmp_path/'prospective',ensemble_path=w,expected_target=211)


def test_strict_source_rejects_unknown_suffix_without_parsing(history,tmp_path):
    source=tmp_path/'source.csv'; extend(history,1245).to_csv(source,index=False)
    with source.open('a') as stream: stream.write('UNSEEN FUTURE ROW\n')
    with pytest.raises(ValueError,match='suffix'): strict_source(source)


def test_existing_ensemble_cannot_be_silently_replaced(tmp_path):
    path=weights(tmp_path)
    config,info=load_existing_ensemble(path)
    assert config['weights']==[.2]+[.1]*8
    assert len(info['sha256'])==64
    data=json.loads(path.read_text()); data['Ensemble[DevelopmentWeights]']['weights']=[1]+[0]*8
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='existing'): load_existing_ensemble(path)
