from pathlib import Path
import json
import numpy as np
import pytest


def test_tensor_cli_no_publication_and_strict_cutoff(tmp_path):
    from src.tensor_cli import guard,load_research_source
    from src.cli import _parser
    path=tmp_path/'future.csv'
    path.write_bytes(Path('data/raw/lotto_history.csv').read_bytes()+b'1246,DO_NOT_PARSE\xff\n')
    with pytest.raises(ValueError,match='unknown suffix'):load_research_source(path)
    with pytest.raises(ValueError):guard('reports/prospective')
    with pytest.raises(SystemExit):_parser().parse_args(['tensor','prepare-freeze'])
    assert _parser().parse_args(['tensor','analyze']).surrogates==199


def test_existing_target_and_archive_publication_guards(tmp_path):
    from src.phase15_freeze import prepare_freeze,PENDING
    with pytest.raises(ValueError,match=PENDING):prepare_freeze(tmp_path/'none',tmp_path/'absent')
    with pytest.raises(ValueError):prepare_freeze(tmp_path/'none',tmp_path/'absent',target=1246)
    assert list(tmp_path.iterdir())==[]


def test_targeted_controls_are_invariant_spectrally():
    from src.analysis.spatiotemporal import iid_surrogate
    from src.tensor_cli import targeted_controls
    result=targeted_controls(iid_surrogate(110,seed=33))
    for row in result:
        assert row['max_spectrum_difference']<1e-10
        assert row['reconstruction_error_difference']<1e-10
        assert row['control'] in ('tensor_time_slice_shuffle','consistent_number_label_shuffle')


def test_frozen_decision_cannot_use_full_scope(tmp_path):
    from src.tensor_cli import freeze_decision
    comparisons=[dict(scope='development',cutoff=900,null_model=n,family=f,adjusted_p=1.)
        for n in ('iid','fixed_margins')
        for f in ('concentration','reconstruction','effective_rank','stability','temporal')]
    raw=dict(draws=900,keys=['A/mode_energy/rank=2'],values=np.array([.2]),metadata=[dict(tensor='A',kind='mode_energy',rank=2)])
    selection=freeze_decision(raw,np.array([1.]),comparisons,tmp_path/'decision.json')
    assert selection['selection']['decision']['status']=='PREDICTIVE_MODEL_NOT_JUSTIFIED'
    assert selection['selection']['later_start']==901
    assert not selection['selection']['prospective_capability_created']
    assert json.loads((tmp_path/'decision.json').read_text())==selection
    with pytest.raises(FileExistsError):freeze_decision(raw,np.array([1.]),comparisons,tmp_path/'decision.json')
    with pytest.raises(ValueError):freeze_decision(raw,np.array([1.]),[dict(r,scope='full') for r in comparisons],tmp_path/'bad.json')


def test_calibration_integrity(tmp_path):
    from src.tensor_cli import load_calibration
    (tmp_path/'calibration_1245.json').write_text(json.dumps({'npz_sha256':'bad'}))
    np.savez_compressed(tmp_path/'calibration_1245.npz',mean=np.ones(2))
    with pytest.raises(ValueError,match='integrity'):load_calibration(tmp_path,1245)


def test_decision_requires_canonical_null_effort_before_freeze(tmp_path):
    from src.tensor_cli import decision
    (tmp_path/'analysis_metadata.json').write_text(json.dumps(dict(replicates_per_null=19,pilots_per_scope=32)))
    with pytest.raises(ValueError,match='199'):decision(None,tmp_path)
    assert not (tmp_path/'selected_configuration.json').exists()


def test_orphan_calibration_and_existing_diagnostics_are_preserved(tmp_path):
    from src.tensor_cli import calibrate,diagnostics
    path=tmp_path/'calibration_1245.npz';path.write_bytes(b'preserve')
    with pytest.raises(ValueError,match='exists'):calibrate(tmp_path,32)
    assert path.read_bytes()==b'preserve'
    path=tmp_path/'decompositions.npz';path.write_bytes(b'preserve')
    with pytest.raises(ValueError,match='exists'):diagnostics(None,tmp_path)
    assert path.read_bytes()==b'preserve'


def canonical_decision_fixture(directory):
    from hashlib import sha256
    import pandas as pd
    from src.analysis.spatiotemporal import iid_surrogate
    from src.analysis.tensor_search import FAMILIES
    x=iid_surrogate(1245,seed=773);families=[FAMILIES[j%5] for j in range(165)]
    keys=[f'cell{j}' for j in range(165)];metadata=[dict(tensor='A',family=f,kind='synthetic') for f in families]
    for n in (900,1245):
        path=directory/f'calibration_{n}.npz'
        np.savez_compressed(path,mean=np.zeros(165),std=np.ones(165),eligible=np.ones(165,dtype=bool))
        (directory/f'calibration_{n}.json').write_text(json.dumps(dict(draws=n,replicates=32,keys=keys,
            families=families,metadata=metadata,npz_sha256=sha256(path.read_bytes()).hexdigest())))
    (directory/'analysis_metadata.json').write_text(json.dumps(dict(replicates_per_null=199,pilots_per_scope=32,
        research_cutoff=1245,development_cutoff=900)))
    (directory/'real_summary.json').write_text(json.dumps({scope:dict(representation_hash=sha256(x[:n].tobytes()).hexdigest())
        for scope,n in [('full',1245),('development',900)]}))
    np.savez_compressed(directory/'development_raw.npz',values=np.zeros(165))
    np.savez_compressed(directory/'null_metrics_development.npz',values=np.ones((398,165)))
    comparisons=[];maxima=[]
    for n in ('iid','fixed_margins'):
        comparisons.extend(dict(scope='development',cutoff=900,null_model=n,family=f,replicates=199,
            real_max=0.,global_p=1.,adjusted_p=1.) for f in FAMILIES)
        maxima.extend(dict(scope='development',null_model=n,replicate=i,**{f:1. for f in FAMILIES}) for i in range(199))
    pd.DataFrame(comparisons).to_csv(directory/'global_null_comparison.csv',index=False)
    pd.DataFrame(maxima).to_csv(directory/'null_maxima.csv',index=False)
    return x


def test_canonical_decision_binds_source_and_artifacts(tmp_path):
    from src.tensor_cli import decision
    x=canonical_decision_fixture(tmp_path);decision(x,tmp_path)
    frozen=json.loads((tmp_path/'selected_configuration.json').read_text())['selection']
    assert frozen['decision']['status']=='PREDICTIVE_MODEL_NOT_JUSTIFIED'
    assert len(frozen['provenance']['artifacts'])==8
    assert len(frozen['provenance']['development_matrix_sha256'])==64


@pytest.mark.parametrize('mutation',['calibration_scope','source_hash','null_maximum','comparison_count','comparison_scope','raw_null'])
def test_canonical_decision_refuses_tampered_artifacts(tmp_path,mutation):
    import pandas as pd
    from src.tensor_cli import decision
    x=canonical_decision_fixture(tmp_path)
    if mutation=='calibration_scope':
        p=tmp_path/'calibration_900.json';m=json.loads(p.read_text());m['draws']=1245;p.write_text(json.dumps(m))
    elif mutation=='source_hash':
        p=tmp_path/'real_summary.json';m=json.loads(p.read_text());m['development']['representation_hash']='bad';p.write_text(json.dumps(m))
    elif mutation=='null_maximum':
        p=tmp_path/'null_maxima.csv';m=pd.read_csv(p);m.loc[0,'stability']=9.;m.to_csv(p,index=False)
    elif mutation=='comparison_count':
        p=tmp_path/'global_null_comparison.csv';m=pd.read_csv(p);m.loc[0,'replicates']=198;m.to_csv(p,index=False)
    elif mutation=='comparison_scope':
        p=tmp_path/'global_null_comparison.csv';m=pd.read_csv(p);m.loc[0,'scope']='full';m.to_csv(p,index=False)
    else:np.savez_compressed(tmp_path/'null_metrics_development.npz',values=np.zeros((398,165)))
    with pytest.raises(ValueError):decision(x,tmp_path)
    assert not (tmp_path/'selected_configuration.json').exists()
