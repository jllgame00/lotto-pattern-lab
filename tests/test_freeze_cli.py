import json
import pytest
from src.cli import main
from src.freeze_artifacts import publish_freeze
from test_freeze_artifacts import payload


def test_offline_evaluation_cli_avoids_canonical_loader(tmp_path,monkeypatch,capsys):
    paths=publish_freeze(payload(),tmp_path)
    result=tmp_path/'result.json'; result.write_text(json.dumps(dict(draw_no=211,main_numbers=[1,2,3,4,5,45],bonus=6)))
    def forbidden(*a,**k): pytest.fail('Evaluator must not load canonical history')
    monkeypatch.setattr('src.cli.load_history',forbidden)
    output=tmp_path/'evaluation.json'
    assert main(['evaluate-freeze',str(paths['snapshot']),str(result),'--output',str(output)])==0
    evaluation=json.loads(output.read_text())
    assert evaluation['models']['GapLogistic']['top6_hits']==5
    assert main(['evaluate-freeze',str(paths['snapshot']),str(result),'--output',str(output)])==1
    assert 'exists' in capsys.readouterr().err.lower()


def test_freeze_cli_is_fixed_to1246_and_prints_hashes(history,tmp_path,monkeypatch,capsys):
    # Stub only heavy generation here; real model integration is tested separately.
    p=payload()
    paths=publish_freeze(p,tmp_path)
    def fake(source,directory,**kwargs):
        assert kwargs['expected_target']==1246
        return paths
    monkeypatch.setattr('src.prospective_experiment.freeze_experiment',fake)
    source=tmp_path/'synthetic.csv'; history.to_csv(source,index=False)
    assert main(['--data',str(source),'freeze-next','--reports-dir',str(tmp_path)])==0
    output=capsys.readouterr().out
    assert 'SHA-256' in output and '1246' in output
