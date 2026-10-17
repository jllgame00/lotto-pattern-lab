import pytest
import json
import numpy as np
from hashlib import sha256
from src.analysis.spatiotemporal import iid_surrogate


def module():
    from src import topology_cli
    return topology_cli


def test_offline_registration_and_no_publication_command():
    from src.cli import _parser
    args=_parser().parse_args(['topology','benchmark'])
    assert args.surrogates==199 and args.workers==3
    with pytest.raises(SystemExit):_parser().parse_args(['topology','publish'])


def test_output_target_archive_guards(tmp_path):
    m=module()
    with pytest.raises(ValueError):m.guard(tmp_path)
    with pytest.raises(ValueError,match='1246'):m.prospective_guard(1246,tmp_path)
    with pytest.raises(ValueError,match='ARCHIVE'):m.prospective_guard(1247,tmp_path)
    (tmp_path/'placeholder').write_text('unverified')
    with pytest.raises(ValueError,match='MODEL'):m.prospective_guard(1247,tmp_path)


@pytest.mark.parametrize('name',['real_summary.json','full_metrics.csv','full_raw.npz','development_metrics.csv',
    'development_raw.npz','binary_series.npy','null_progress.jsonl','null_metrics_full.npz',
    'null_metrics_development.npz','null_maxima.csv','global_null_comparison.csv','analysis_metadata.json'])
def test_existing_complete_or_partial_analysis_is_preserved(tmp_path,name):
    output=tmp_path/name;output.write_text('prior evidence')
    with pytest.raises(FileExistsError):module().analyze(iid_surrogate(1245,seed=23),tmp_path,199,1)
    assert output.read_text()=='prior evidence' and list(tmp_path.iterdir())==[output]


def test_canonical_source_cutoff(tmp_path):
    m=module()
    assert m.canonical_matrix(iid_surrogate(1245,seed=23)).shape==(1245,45)
    for n in (900,1246):
        with pytest.raises(ValueError):m.canonical_matrix(iid_surrogate(n,seed=23))
    assert list(tmp_path.iterdir())==[]


def write_calibration(directory,n,replicates=32,seed=231001):
    path=directory/f'calibration_{n}.npz'
    np.savez_compressed(path,mean=np.zeros(1),std=np.ones(1),eligible=np.ones(1,dtype=bool))
    (directory/f'calibration_{n}.json').write_text(json.dumps(dict(draws=n,replicates=replicates,
        seed=seed,npz_sha256=sha256(path.read_bytes()).hexdigest())),encoding='utf-8')


@pytest.mark.parametrize('n,field,value',[(900,'replicates',4),(900,'seed',23),(1245,'replicates',4),(1245,'seed',23)])
def test_both_calibrations_must_match_frozen_protocol(tmp_path,n,field,value):
    for cutoff in (1245,900):write_calibration(tmp_path,cutoff,**({field:value} if cutoff==n else {}))
    with pytest.raises(ValueError,match='calibration protocol'):module().canonical_calibrations(tmp_path)


def test_canonical_calibrations_load_both_scopes(tmp_path):
    for cutoff in (1245,900):write_calibration(tmp_path,cutoff)
    assert list(module().canonical_calibrations(tmp_path))==[1245,900]


def test_selection_rejects_source_hash_before_freezing(tmp_path):
    meta=dict(research_cutoff=1245,development_cutoff=900,seed=230042,pilot_seed=231001,
        pilots_per_scope=32,replicates_per_null=199,input_matrix_hash='different source')
    (tmp_path/'analysis_metadata.json').write_text(json.dumps(meta),encoding='utf-8')
    with pytest.raises(ValueError,match='source hash'):module().select(iid_surrogate(1245,seed=23),tmp_path)
    assert not (tmp_path/'selected_configuration.json').exists()
