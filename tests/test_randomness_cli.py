from pathlib import Path
import numpy as np
import pytest


def test_frozen_source_guard_and_no_prediction_command(tmp_path):
    from src.randomness_cli import load_source,guard,add_commands
    import argparse
    source=Path(__file__).resolve().parents[1]/'data/raw/lotto_history.csv'
    data,x=load_source(source);assert len(data)==len(x)==1245
    poison=tmp_path/'future.csv';poison.write_bytes(source.read_bytes()+b'\n1246,forbidden')
    with pytest.raises(ValueError):load_source(poison)
    with pytest.raises(ValueError):guard(tmp_path)
    parser=argparse.ArgumentParser();commands=parser.add_subparsers(dest='command');add_commands(commands)
    for action in ('predict','publish','prepare-freeze'):
        with pytest.raises(SystemExit):parser.parse_args(['randomness-battery',action])


def test_archives_are_verified_read_only_and_failures_are_visible(tmp_path):
    from src.randomness_cli import archive_inventory,verified_archive
    from hashlib import sha256
    import json
    p=tmp_path/'archive';p.mkdir();artifact=p/'frozen.json';artifact.write_bytes(b'original')
    record=p/'frozen_integrity.json';record.write_text(json.dumps({'frozen.json':sha256(artifact.read_bytes()).hexdigest()}))
    before={q.name:q.read_bytes() for q in p.iterdir()}
    assert archive_inventory(p)['status']=='VERIFIED'
    assert verified_archive(p)['status']=='VERIFIED'
    assert before=={q.name:q.read_bytes() for q in p.iterdir()}
    artifact.write_bytes(b'bad');failed=archive_inventory(p)
    assert failed['status']=='PROSPECTIVE_ARCHIVE_INTEGRITY_FAILURE'
    assert failed['checks'][0]['verified'] is False
    with pytest.raises(ValueError,match='PROSPECTIVE_ARCHIVE_STATUS=FAILURE'):
        verified_archive(p)


def test_primary_status_uses_full_global6_only_not_era_or_track3():
    from src.analysis.randomness_omnibus import scientific_status
    rows=[dict(scope='full',track='iid',track_adjusted_p=.03,overall_adjusted_p=.06),
          dict(scope='early',track='fixed_margins',overall_adjusted_p=.03)]
    assert scientific_status(rows)=='TESTED / INCONCLUSIVE'
    rows[0]['overall_adjusted_p']=.03
    assert scientific_status(rows)=='EVIDENCE AGAINST IID RANDOMNESS'
    rows.append(dict(scope='full',track='fixed_margins',overall_adjusted_p=.03))
    assert scientific_status(rows)=='EVIDENCE OF TEMPORAL/RELATIONAL STRUCTURE'
