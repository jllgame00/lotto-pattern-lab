from pathlib import Path
import json
import numpy as np
import pytest


def test_source_future_suffix_and_prospective_target_are_rejected(tmp_path):
    from src.symbolic_cli import load_source,prospective_guard,guard
    source=Path(__file__).resolve().parents[1]/'data/raw/lotto_history.csv'
    data,x=load_source(source);assert len(data)==len(x)==1245
    future=tmp_path/'future.csv';future.write_bytes(source.read_bytes()+b'\n1246,forbidden')
    with pytest.raises(ValueError):load_source(future)
    with pytest.raises(ValueError):guard(tmp_path)
    with pytest.raises(ValueError,match='1246'):prospective_guard(1246,'VERIFIED')
    with pytest.raises(ValueError,match='PREDICTIVE_MODEL_NOT_JUSTIFIED'):prospective_guard(1247,'VERIFIED')
    with pytest.raises(ValueError,match='INTEGRITY_FAILURE'):prospective_guard(1247,'PROSPECTIVE_ARCHIVE_INTEGRITY_FAILURE')


def test_maximum_audit_uses_upper_tail_and_excludes_constant_cells():
    from src.symbolic_cli import verify_maxima
    from src.analysis.symbolic_search import FAMILIES
    c=dict(mean=np.zeros(18),std=np.ones(18),eligible=np.tile([True,True,False],6),families=[f for f in FAMILIES for _ in range(3)])
    values=np.array([[-10,3,99]*6,[5,-7,99]*6],float)
    expected={f:np.array([3.,5.]) for f in FAMILIES}
    verify_maxima(values,c,expected)
    with pytest.raises(AssertionError):verify_maxima(values,c,{**expected,FAMILIES[0]:np.array([10.,7.])})


def test_metric_export_keeps_word_support_separate_from_calibration_eligibility(tmp_path):
    import pandas as pd
    from src.symbolic_cli import save_metrics
    from src.analysis.symbolic_search import fit_calibration,metric_vector
    from src.analysis.spatiotemporal import iid_surrogate
    c=fit_calibration(900,replicates=4);raw=metric_vector(iid_surrogate(900,seed=11))
    save_metrics(tmp_path,'test',raw,c)
    table=pd.read_csv(tmp_path/'test_metrics.csv')
    assert len(table)==304 and table.eligible.all()
    assert 'eligible_word_count' in table
    with np.load(tmp_path/'test_raw.npz') as f:np.testing.assert_array_equal(f['values'],raw['values'])
