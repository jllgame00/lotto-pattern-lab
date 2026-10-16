import io
from unittest.mock import patch

import pandas as pd
import pytest

from src.research_seal import load_research_history, assert_open, prefix_hash
from src.analysis.features import build_features
from src.models.predictive import LogisticModel
from test_features import extend


def test_loader_never_requests_sealed_line(history,tmp_path):
    text=extend(history,1244).to_csv(index=False)
    class SealedStream(io.StringIO):
        def readline(self,*args):
            if self.tell()>=len(text):
                raise AssertionError('Attempted to read sealed line')
            return super().readline(*args)
    with patch('pathlib.Path.open',return_value=SealedStream(text)):
        result=load_research_history(tmp_path/'canonical.csv')
    assert result.draw_no.max()==1244 and len(result)==1244


def test_suffix_cannot_affect_prefix_hash(history,tmp_path):
    path=tmp_path/'history.csv'
    text=extend(history,1244).to_csv(index=False)
    path.write_text(text+'SEALED MALFORMED CONTENT\n',encoding='utf-8',newline='')
    a=prefix_hash(path)
    assert len(load_research_history(path))==1244
    path.write_text(text+'OTHER SEALED CONTENT\n',encoding='utf-8',newline='')
    assert prefix_hash(path)==a


def test_feature_and_model_boundaries(history):
    with pytest.raises(ValueError,match='sealed'): assert_open(pd.DataFrame({'target_draw':[1245]}),'target_draw')
    with pytest.raises(ValueError,match='sealed'): build_features(extend(history,1245))
    with pytest.raises(ValueError,match='sealed'): build_features(extend(history,1244),include_current=True)
    with pytest.raises(ValueError,match='sealed'):
        LogisticModel().fit(pd.DataFrame({'target_draw':[1245]}),cutoff=1245)


def test_cli_current_does_not_load_when_canonical_is_sealed(monkeypatch,capsys):
    from src.cli import main
    def forbidden(*args,**kwargs): raise AssertionError('Must block before reading canonical data')
    monkeypatch.setattr('src.cli.load_history',forbidden)
    assert main(['predict-current'])==1
    assert 'sealed' in capsys.readouterr().err


def test_alternate_path_cannot_predict_sealed_target(history,tmp_path,capsys):
    from src.cli import main
    path=tmp_path/'prefix.csv'
    extend(history,1244).to_csv(path,index=False)
    assert main(['--data',str(path),'candidates'])==1
    assert 'sealed' in capsys.readouterr().err


def test_collect_cannot_copy_canonical_or_query_latest(tmp_path,monkeypatch,capsys):
    from src.cli import main, DEFAULT_DATA
    def forbidden(*args,**kwargs): raise AssertionError('Collector must not run')
    monkeypatch.setattr('src.cli.import_history',forbidden)
    monkeypatch.setattr('src.cli.collect_history',forbidden)
    base=['--data',str(tmp_path/'output.csv'),'collect']
    assert main(base+['--input',str(DEFAULT_DATA),'--source-label','copy'])==1
    assert main(base+['--end','1244'])==1  # network batches may include later draws
    assert 'sealed' in capsys.readouterr().err


def test_collect_cannot_read_suffix_of_copied_source(history,tmp_path,monkeypatch):
    from src.cli import main
    source=tmp_path/'copy.csv'
    source.write_text(extend(history,1244).to_csv(index=False,lineterminator='\n')+'SEALED INVALID SUFFIX\n',newline='')
    def forbidden(*args,**kwargs): raise AssertionError('Must not reach full-file importer')
    monkeypatch.setattr('src.cli.import_history',forbidden)
    assert main(['--data',str(tmp_path/'destination.csv'),'collect','--input',str(source),'--source-label','copy'])==1
