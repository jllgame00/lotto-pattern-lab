from pathlib import Path
from hashlib import sha256
import json
import numpy as np
import pytest


def test_archive_inventory_supports_both_record_schemas_and_detects_tamper(tmp_path):
    from src.optimal_transport_cli import archive_inventory
    archive=tmp_path/'archive'
    assert archive_inventory(archive)['status']=='ABSENT'
    archive.mkdir();a=archive/'snapshot.json';a.write_bytes(b'{"frozen":true}')
    digest=sha256(a.read_bytes()).hexdigest()
    (archive/'first_integrity.json').write_text(json.dumps({'algorithm':'SHA-256','files':{'snapshot.json':digest}}))
    (archive/'second_integrity.json').write_text(json.dumps({'snapshot.json':digest}))
    before={p.name:p.read_bytes() for p in archive.iterdir()}
    result=archive_inventory(archive)
    assert result['status']=='VERIFIED' and len(result['checks'])==2
    assert before=={p.name:p.read_bytes() for p in archive.iterdir()}
    a.write_bytes(b'changed')
    assert archive_inventory(archive)['status']=='PROSPECTIVE_ARCHIVE_INTEGRITY_FAILURE'


def test_scope_output_and_prospective_restrictions(tmp_path):
    from src.optimal_transport_cli import guard, canonical_matrix, prospective_guard
    from src.analysis.spatiotemporal import iid_surrogate
    with pytest.raises(ValueError):guard(tmp_path)
    with pytest.raises(ValueError):canonical_matrix(iid_surrogate(1246,seed=1))
    with pytest.raises(ValueError,match='1246'):prospective_guard(1246,'VERIFIED')
    with pytest.raises(ValueError,match='PREDICTIVE_MODEL_NOT_JUSTIFIED'):prospective_guard(1247,'VERIFIED')
    with pytest.raises(ValueError,match='INTEGRITY_FAILURE'):prospective_guard(1247,'PROSPECTIVE_ARCHIVE_INTEGRITY_FAILURE')


def test_phase24_source_rejects_future_suffix_before_parsing(tmp_path):
    from src.optimal_transport_cli import load_source
    source=Path(__file__).resolve().parents[1]/'data/raw/lotto_history.csv'
    data,x=load_source(source)
    assert len(data)==len(x)==1245
    poisoned=tmp_path/'poison.csv';poisoned.write_bytes(source.read_bytes()+b'\n1246,forbidden')
    with pytest.raises(ValueError):load_source(poisoned)


def test_independent_maxima_audit_detects_different_cell_tamper():
    from src.optimal_transport_cli import verify_maxima
    from src.analysis.optimal_transport_search import FAMILIES
    c=dict(mean=np.zeros(12),std=np.ones(12),eligible=np.ones(12,bool),families=[f for f in FAMILIES for _ in range(2)])
    values=np.array([[1.,-4.]*6,[5.,-2.]*6])
    expected={f:np.array([4.,5.]) for f in FAMILIES}
    verify_maxima(values,c,expected)
    with pytest.raises(AssertionError):verify_maxima(values,c,{**expected,FAMILIES[0]:np.array([1.,5.])})
