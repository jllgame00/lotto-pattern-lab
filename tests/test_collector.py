import json
import pandas as pd
import pytest

from src.collect.collector import collect_history, import_history
from src.collect.dataset import DatasetError
from src.collect.sources import OfficialSource, SourceError, parse_official_payload


def test_parse_official_batch_and_wrong_schema():
    item = dict(ltEpsd=1, ltRflYmd='20021207', bnsWnNo=16,
                **{f'tm{i}WnNo': n for i, n in enumerate([10,23,29,33,37,40],1)})
    rows = parse_official_payload({'data': {'list': [item]}})
    assert rows[0]['draw_date'] == '2002-12-07'
    assert rows[0]['num6'] == 40
    assert rows[0]['draw_no'] == 1
    for payload in ({}, {'data': {}}, {'data': {'list': [dict(ltEpsd=1)]}}):
        with pytest.raises(SourceError):
            parse_official_payload(payload)


def test_non_json_response_is_not_end_of_history():
    source = OfficialSource(get_json=lambda url: (_ for _ in ()).throw(SourceError('HTML block page')))
    with pytest.raises(SourceError, match='HTML'):
        source.fetch_batch(1)


def test_import_rerun_atomic_conflict_and_provenance(tmp_path, history):
    incoming, target = tmp_path/'incoming.csv', tmp_path/'history.csv'
    pd.concat([history.iloc[::-1], history.iloc[:1]]).to_csv(incoming, index=False)
    report = import_history(target, incoming, source_label='test fixture')
    assert report['added'] == 12 and report['missing_draws'] == []
    before = target.read_bytes()
    report2 = import_history(target, incoming, source_label='test fixture')
    assert report2['added'] == 0
    assert target.read_bytes() == before
    assert json.loads(target.with_suffix('.metadata.json').read_text())['sha256']
    history.loc[0, 'bonus'] = 44
    history.to_csv(incoming, index=False)
    with pytest.raises(DatasetError, match='Conflicting'):
        import_history(target, incoming, source_label='test fixture')
    assert target.read_bytes() == before


def test_partial_collection_reports_missing_and_resumes(tmp_path, history):
    class Source:
        label = 'test source'
        def latest_draw(self): return 12
        def fetch_batch(self, n):
            if n == 7: raise SourceError('connection failed')
            return history[history.draw_no == n].to_dict('records')
    path = tmp_path/'history.csv'
    report = collect_history(path, source=Source())
    assert report['missing_draws'] == [7,8,9,10,11,12]
    assert report['errors'] and report['rows'] == 6
    class Recovered(Source):
        def fetch_batch(self, n): return history[history.draw_no >= n].to_dict('records')
    report = collect_history(path, source=Recovered())
    assert report['added'] == 6 and report['complete']
    assert len(pd.read_csv(path)) == 12


def test_wrong_draw_and_invalid_batch_never_written(tmp_path, history):
    class WrongSource:
        label = 'wrong source'
        def latest_draw(self): return 12
        def fetch_batch(self, n): return history.iloc[1:2].to_dict('records')
    path = tmp_path/'history.csv'
    report = collect_history(path, source=WrongSource())
    assert report['rows'] == 0 and report['errors']
    assert not path.exists()


def test_import_null_draw_number_preserves_data_and_metadata(tmp_path, history):
    incoming, target = tmp_path/'incoming.csv', tmp_path/'history.csv'
    history.to_csv(incoming, index=False)
    import_history(target, incoming, source_label='fixture')
    original = target.read_bytes()
    metadata = target.with_suffix('.metadata.json').read_bytes()
    invalid = history.iloc[:1].copy()
    invalid['draw_no'] = None
    pd.concat([history, invalid]).to_csv(incoming, index=False)
    with pytest.raises(DatasetError):
        import_history(target, incoming, source_label='invalid fixture')
    assert target.read_bytes() == original
    assert target.with_suffix('.metadata.json').read_bytes() == metadata
