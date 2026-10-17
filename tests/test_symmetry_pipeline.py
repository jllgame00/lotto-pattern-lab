import json
from pathlib import Path
import numpy as np
import pytest


def test_offline_source_output_and_publication_guards(tmp_path):
    from src.symmetry_cli import guard,load_research_source
    from src.cli import _parser
    path=tmp_path/'future.csv';path.write_bytes(Path('data/raw/lotto_history.csv').read_bytes()+b'1246,UNPARSED\xff\n')
    with pytest.raises(ValueError,match='unknown suffix'):load_research_source(path)
    with pytest.raises(ValueError):guard('reports/prospective')
    with pytest.raises(SystemExit):_parser().parse_args(['symmetry','prepare-freeze'])
    args=_parser().parse_args(['symmetry','analyze']);assert args.surrogates==199
    from src.phase15_freeze import prepare_freeze,PENDING
    with pytest.raises(ValueError,match=PENDING):prepare_freeze(tmp_path/'none',tmp_path/'absent')
    with pytest.raises(ValueError):prepare_freeze(tmp_path/'none',tmp_path/'absent',target=1246)


def test_calibration_hash_and_orphan_preservation(tmp_path):
    from src.symmetry_cli import load_calibration,calibrate
    path=tmp_path/'calibration_1245.npz';path.write_bytes(b'preserve')
    with pytest.raises(ValueError,match='exists'):calibrate(tmp_path,32)
    assert path.read_bytes()==b'preserve'
    (tmp_path/'calibration_1245.json').write_text(json.dumps(dict(npz_sha256='bad')))
    with pytest.raises(ValueError,match='integrity'):load_calibration(tmp_path,1245)


def test_pooled_interval_uses_whole_draw_blocks_deterministically():
    from src.analysis.spatiotemporal import iid_surrogate
    from src.symmetry_cli import pooled_uncertainty
    x=iid_surrogate(260,seed=18)
    a=pooled_uncertainty(x,replicates=100);b=pooled_uncertainty(x,replicates=100)
    assert a==b and len(a)==9
    for row in a:
        assert row['ci_low']<=row['ci_high'] and row['block']==52
        assert row['sources']>0 and row['target_end']==260


def test_noncanonical_null_effort_cannot_start_selection(tmp_path):
    from src.symmetry_cli import select
    (tmp_path/'analysis_metadata.json').write_text(json.dumps(dict(replicates_per_null=19,pilots_per_scope=32)))
    with pytest.raises(ValueError,match='199'):select(None,tmp_path)
    assert not (tmp_path/'selected_configuration.json').exists()


def test_center_reference_with_no_center_is_undefined_not_error():
    from src.symmetry_cli import center_reference
    x=np.zeros((208,45),dtype=bool);x[:,:6]=True
    rows=center_reference(x)
    assert len(rows)==9 and all(r['support']==0 and np.isnan(r['rate']) for r in rows)


def test_side_balance_exact_expectation_is_normalized():
    from src.symmetry_cli import side_balance_expectation
    r=side_balance_expectation()
    assert sum(a['probability'] for a in r['distribution'])==pytest.approx(1)
    assert r['expected_left']==pytest.approx(22*6/45)
    assert r['expected_right']==r['expected_left']
    assert r['center_probability']==pytest.approx(6/45)
    assert 0<r['expected_imbalance']<6


def test_shift_opportunities_and_selected_pair_rolling_are_preserved(tmp_path):
    import pandas as pd
    from src.analysis.spatiotemporal import iid_surrogate
    from src.symmetry_cli import diagnostic_details
    x=iid_surrogate(260,seed=91)
    pd.DataFrame([dict(family=f,kind=k,z=1.,lag=1,source=1,target=45,pair=1)
        for f,k in [('pair','pair_risk'),('anti','negative_pair_risk'),('asymmetry','directional_difference')]]).to_csv(tmp_path/'full_metrics.csv',index=False)
    (tmp_path/'real_summary.json').write_text(json.dumps(dict(full=dict(leaders={}))))
    diagnostic_details(x,tmp_path)
    shift=pd.read_csv(tmp_path/'shift_relations.csv');rolling=pd.read_csv(tmp_path/'pair_rolling.csv')
    assert len(shift)==45 and len(rolling)==78
    assert all(shift.hits<=shift.sources) and all(shift.valid_source_labels>0)
    assert set(rolling.minimum_support)=={10}
    with pytest.raises(ValueError):diagnostic_details(x,tmp_path)
