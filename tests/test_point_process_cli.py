from pathlib import Path
import numpy as np
import pytest


def test_output_guard(tmp_path):
    from src.point_process_cli import guard
    with pytest.raises(ValueError):guard(tmp_path)


def test_cli_registration():
    from src.cli import _parser
    args=_parser().parse_args(['point-process','analyze'])
    assert args.surrogates==199 and args.workers==4


def test_source_seal_before_analysis(tmp_path):
    from src.point_process_cli import analyze
    x=np.zeros((1246,45),dtype=bool);x[:,:6]=True
    with pytest.raises(ValueError):analyze(x,tmp_path,199,1)
    assert not list(tmp_path.iterdir())


def test_prospective_target_and_archive_guards(tmp_path):
    from src.phase15_freeze import prepare_freeze
    with pytest.raises(ValueError,match='1247'):prepare_freeze(tmp_path/'missing.json',tmp_path/'archive',target=1246)
    with pytest.raises(ValueError,match='PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION'):
        prepare_freeze(tmp_path/'missing.json',tmp_path/'archive',target=1247)


def test_existing_calibration_protocol_cannot_be_relabelled(tmp_path,monkeypatch):
    import src.point_process_cli as cli
    (tmp_path/'calibration_1245.json').write_text('{}')
    monkeypatch.setattr(cli,'load_calibration',lambda *args:dict(replicates=4,seed=201001))
    with pytest.raises(ValueError,match='protocol'):cli.calibrate(tmp_path,32)


def test_development_checks_both_pilot_scopes(tmp_path,monkeypatch):
    import json
    import src.point_process_cli as cli
    (tmp_path/'analysis_metadata.json').write_text(json.dumps(dict(replicates_per_null=199,pilots_per_scope=32,research_cutoff=1245,development_cutoff=900)))
    monkeypatch.setattr(cli,'load_calibration',lambda directory,n:dict(replicates=32 if n==1245 else 4,seed=201001))
    with pytest.raises(ValueError,match='Both calibration'):cli.validate_development(None,tmp_path)


