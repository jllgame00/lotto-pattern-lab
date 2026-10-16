import json
from pathlib import Path
import pandas as pd
import pytest
from test_features import extend
from src.prospective import load_prospective_source, freeze_snapshot


def test_prospective_contents_immutable_and_no_fetch(history,tmp_path,monkeypatch):
    import socket
    monkeypatch.setattr(socket.socket,'connect',lambda *a,**kw:pytest.fail('Must not fetch'))
    path=tmp_path/'source.csv'; extend(history,130).to_csv(path,index=False)
    a=freeze_snapshot(path,tmp_path/'snapshots',seed=7)
    b=freeze_snapshot(path,tmp_path/'snapshots',seed=7)
    assert a!=b and a.exists()
    x=json.loads(a.read_text()); y=json.loads(b.read_text())
    assert x['target_draw']==131 and x['latest_included_draw']==130
    assert len(x['canonical_dataset_sha256'])==64
    assert x['models']==y['models']
    for model in x['models'].values():
        assert len(model['scores'])==45
        assert len(model['rankings']['12'])==12
        assert len(model['portfolios']['coverage'])==20
    assert x['target_result_retrieved'] is False
    assert x['prospective_status']=='unverified: caller must establish target was unseen at freeze time'


def test_prospective_loader_never_parses_beyond_fixed_canonical_limit(history,tmp_path):
    path=tmp_path/'source.csv'
    source=extend(history,1245)
    source.to_csv(path,index=False)
    with path.open('a') as stream: stream.write('DO NOT PARSE FUTURE RESULT\n')
    data,digest=load_prospective_source(path)
    assert len(data)==1245
    assert len(digest)==64


def test_prospective_refuses_noncontiguous_source(history,tmp_path):
    path=tmp_path/'source.csv'; history.iloc[::-1].to_csv(path,index=False)
    with pytest.raises(ValueError): load_prospective_source(path)


def test_unavailable_git_status_is_unknown_not_clean(history,tmp_path,monkeypatch):
    import subprocess
    def unavailable(*args,**kwargs): raise OSError('git unavailable')
    monkeypatch.setattr(subprocess,'check_output',unavailable)
    path=tmp_path/'source.csv'; extend(history,110).to_csv(path,index=False)
    snapshot=json.loads(freeze_snapshot(path,tmp_path/'reports').read_text())
    assert snapshot['git_commit'] is None
    assert snapshot['git_dirty'] is None
