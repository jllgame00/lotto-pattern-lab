import json
from hashlib import sha256
import pytest


def test_separate_immutable_phase6_freeze(history,tmp_path,monkeypatch):
    from test_features import extend
    from src.phase6_freeze import freeze_2d,verify_2d
    # A sentinel stands for the existing Phase5 registry and snapshot.
    phase5=tmp_path/'phase5'; phase5.mkdir()
    old=phase5/'registry.csv'; old.write_bytes(b'original immutable registry\n')
    source=tmp_path/'synthetic.csv'; extend(history,120).to_csv(source,index=False)
    import socket
    monkeypatch.setattr(socket,'create_connection',lambda *a,**k:pytest.fail('Network forbidden'))
    directory=phase5/'phase6'
    paths=freeze_2d(source,directory,expected_target=121)
    payload=verify_2d(paths['snapshot'])
    assert payload['target_draw']==121 and payload['training_cutoff']==120
    assert payload['status']=='FROZEN_UNEVALUATED'
    assert payload['phase']==6 and payload['target_result_retrieved'] is False
    assert set(payload['models'])=={'TranslationModel','ChainModel','Combined2D'}
    for model in payload['models'].values():
        assert len(model['scores'])==45 and set(model['ranking'])==set(range(1,46))
        for k in (6,8,10,12,15): assert model['top_k'][str(k)]==model['ranking'][:k]
        for group in model['portfolios'].values():
            for budget,tickets in group.items():
                assert len(tickets)==len(set(map(tuple,tickets)))==int(budget)
    assert old.read_bytes()==b'original immutable registry\n'
    before=paths['snapshot'].read_bytes()
    with pytest.raises(ValueError,match='already'): freeze_2d(source,directory,expected_target=121)
    assert paths['snapshot'].read_bytes()==before
    registry=(directory/'registry.csv').read_text()
    assert 'FROZEN_UNEVALUATED' in registry and sha256(before).hexdigest() in registry
    paths['manifest'].write_text('tampered',encoding='utf-8')
    with pytest.raises(ValueError,match='integrity'): verify_2d(paths['snapshot'])


def test_freeze_rejects_wrong_cutoff_before_predictions(history,tmp_path):
    from test_features import extend
    from src.phase6_freeze import freeze_2d
    source=tmp_path/'synthetic.csv'; extend(history,120).to_csv(source,index=False)
    with pytest.raises(ValueError,match='target'): freeze_2d(source,tmp_path/'out',expected_target=1246)
    assert not (tmp_path/'out'/'registry.csv').exists()


def test_phase6_cli_is_separate(history,tmp_path):
    from test_features import extend
    from src.cli import main
    source=tmp_path/'synthetic.csv'; extend(history,120).to_csv(source,index=False)
    # Actual CLI only accepts the declared1246; fixture fails without generating predictions.
    assert main(['--data',str(source),'freeze-2d','--reports-dir',str(tmp_path/'out')])==1


def test_registry_paths_bound_to_artifacts(history,tmp_path):
    from test_features import extend
    from src.phase6_freeze import freeze_2d,verify_2d
    source=tmp_path/'synthetic.csv'; extend(history,120).to_csv(source,index=False)
    directory=tmp_path/'phase6'; paths=freeze_2d(source,directory,expected_target=121)
    registry=directory/'registry.csv'; contents=registry.read_text()
    registry.write_text(contents.replace(paths['snapshot'].name,'wrong.json'))
    with pytest.raises(ValueError,match='path'): verify_2d(paths['snapshot'])
