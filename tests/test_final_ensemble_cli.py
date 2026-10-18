import json
from pathlib import Path
import pytest


def test_seals_are_immutable_and_tampering_is_detected(tmp_path):
    from src.final_ensemble_cli import write_seal,read_seal
    p=tmp_path/'seal.json';write_seal(p,{'cutoff':1245})
    assert read_seal(p)=={'cutoff':1245}
    with pytest.raises(FileExistsError):write_seal(p,{'cutoff':1245})
    a=json.loads(p.read_text());a['payload']['cutoff']=1246;p.write_text(json.dumps(a))
    with pytest.raises(ValueError):read_seal(p)


def test_configuration_freeze_is_configuration_only_and_negative_not_ready():
    from src.final_ensemble_cli import configuration_record
    gate=dict(passed=False,selected=dict(id='equal_all',weights=[.25]*4),best_single='GapLogistic')
    config=configuration_record(gate,'NO_ENSEMBLE_ADVANTAGE_ESTABLISHED',git_sha='a'*40,data_sha='b'*64,archive_status='VERIFIED')
    assert not config['ready_for_1247'] and config['intended_future_target']==1247
    assert config['historical_selection_cutoff']==1245
    assert not {'predictions','numbers','tickets','ranking'}&set(config)
    with pytest.raises(ValueError):configuration_record(gate,'NO_ENSEMBLE_ADVANTAGE_ESTABLISHED',git_sha='a'*40,data_sha='b'*64,archive_status='FAILURE')


def test_no_predict_import_or_publication_command():
    import argparse
    from src.final_ensemble_cli import add_commands
    p=argparse.ArgumentParser();commands=p.add_subparsers();add_commands(commands)
    for action in ('predict','import','publish','draw1247'):
        with pytest.raises(SystemExit):p.parse_args(['final-ensemble',action])


def test_source_future_suffix_rejected_before_analysis(tmp_path):
    from src.final_ensemble_cli import load_source
    root=Path(__file__).resolve().parents[1]
    path=tmp_path/'bad.csv';path.write_bytes((root/'data/raw/lotto_history.csv').read_bytes()+b'\n1246,forbidden')
    with pytest.raises(ValueError):load_source(path)


def test_final_lock_prevents_second_model_selection_evaluation(tmp_path):
    from src.final_ensemble_cli import begin_final
    begin_final(tmp_path,'a'*64)
    with pytest.raises(FileExistsError):begin_final(tmp_path,'a'*64)


def test_failed_replay_audit_cannot_be_bypassed_by_later_command(tmp_path,monkeypatch):
    import src.final_ensemble_cli as cli
    monkeypatch.setattr(cli,'protocol',lambda _: {})
    (tmp_path/'replay_audit_26.json').write_text(json.dumps(dict(checks=[dict(matches=False)])))
    with pytest.raises(ValueError,match='replay audit'):cli.panels(tmp_path)


def test_failed_real_gate_uses_zero_promoted_gain_and_no_pvalue_claim():
    import pandas as pd
    from src.final_ensemble_cli import placebo_comparison
    table=pd.DataFrame([dict(kind='random_weight',final_rank_gain=-.5,final_promoted_gain=0),
                        dict(kind='random_weight',final_rank_gain=.5,final_promoted_gain=.5)])
    r=placebo_comparison(table,real_gain=-1,gate_passed=False)
    assert r['observed_promoted_gain']==0
    assert r['promotion_tail_fractions']['random_weight'] is None
    assert r['raw_tail_fractions']['random_weight']==1


def test_incomplete_final_evidence_cannot_satisfy_empty_all_checks():
    import pandas as pd
    from src.final_ensemble_cli import validate_completion
    with pytest.raises(ValueError,match='Incomplete'):
        validate_completion(pd.DataFrame(),pd.DataFrame(),pd.DataFrame(),'GapLogistic')
