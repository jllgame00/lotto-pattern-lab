import json
import socket
import pytest
from src.freeze_artifacts import digest


def test_complete_phase7_generation_offline_and_nonoverwrite(history,tmp_path,monkeypatch):
    from test_features import extend
    from src.phase7_freeze import freeze_gap3d
    from src.phase7_artifacts import verify_gap3d
    data=extend(history,120); source=tmp_path/'history.csv'; data.to_csv(source,index=False)
    root=tmp_path/'prospective'; root.mkdir(); prior=root/'earlier.json'; prior.write_text('immutable')
    protected={'earlier.json':digest(prior)}
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('Network forbidden'))
    paths=freeze_gap3d(source,root/'phase7',expected_target=121,protected=protected)
    p=verify_gap3d(paths['snapshot'])
    assert p['target_draw']==121 and p['training_cutoff']==120 and not p['future_result_accessed']
    assert p['dataset_hash']==digest(source) and p['sources'] and p['source_hashes']
    assert all(v['encoder']['training_cutoff']==120 for v in p['fitted_models'].values())
    assert all(len(t['ranking'])==45 for t in p['models'].values())
    before={f:f.read_bytes() for f in root.rglob('*') if f.is_file()}
    with pytest.raises(ValueError,match='already'): freeze_gap3d(source,root/'phase7',expected_target=121,protected=protected)
    assert all(f.read_bytes()==content for f,content in before.items())


def test_freeze_rejects_cutoff_and_changed_provenance_before_artifacts(history,tmp_path):
    from test_features import extend
    from src.phase7_freeze import freeze_gap3d
    data=extend(history,120); source=tmp_path/'history.csv'; data.to_csv(source,index=False)
    with pytest.raises(ValueError,match='cutoff'): freeze_gap3d(source,tmp_path/'phase7',expected_target=122,protected={})
    assert not (tmp_path/'phase7').exists()
