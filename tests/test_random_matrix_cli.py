from pathlib import Path
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def module():
    from src import random_matrix_cli
    return random_matrix_cli


def test_offline_cli_registration_and_no_publication():
    from src.cli import _parser
    args=_parser().parse_args(['random-matrix','benchmark'])
    assert args.surrogates==199 and args.workers==3
    with pytest.raises(SystemExit):_parser().parse_args(['random-matrix','publish'])


def test_output_and_prospective_guards(tmp_path):
    m=module()
    with pytest.raises(ValueError):m.guard(tmp_path)
    with pytest.raises(ValueError,match='1246'):m.prospective_guard(1246,tmp_path)
    with pytest.raises(ValueError,match='ARCHIVE'):m.prospective_guard(1247,tmp_path)
    (tmp_path/'evidence').write_text('placeholder')
    with pytest.raises(ValueError,match='MODEL'):m.prospective_guard(1247,tmp_path)


def test_canonical_cutoff_rejects_future_before_any_output(tmp_path):
    m=module()
    assert m.canonical_matrix(iid_surrogate(1245,seed=22)).shape==(1245,45)
    for n in (900,1246):
        with pytest.raises(ValueError):m.canonical_matrix(iid_surrogate(n,seed=22))
    assert list(tmp_path.iterdir())==[]


def test_analysis_refuses_existing_evidence_before_loading_calibration(tmp_path):
    output=tmp_path/'real_summary.json';output.write_text('existing')
    with pytest.raises(FileExistsError):module().analyze(iid_surrogate(1245,seed=22),tmp_path,199,1)
    assert output.read_text()=='existing'
    assert list(tmp_path.iterdir())==[output]


@pytest.mark.parametrize('name',['full_metrics.csv','full_raw.npz','development_metrics.csv','development_raw.npz',
    'binary_series.npy','null_metrics_full.npz','null_metrics_development.npz','null_maxima.csv','global_null_comparison.csv'])
def test_analysis_preserves_orphan_partial_outputs(tmp_path,name):
    output=tmp_path/name;output.write_bytes(b'prior partial evidence')
    with pytest.raises(FileExistsError):module().analyze(iid_surrogate(1245,seed=22),tmp_path,199,1)
    assert output.read_bytes()==b'prior partial evidence'
    assert list(tmp_path.iterdir())==[output]
