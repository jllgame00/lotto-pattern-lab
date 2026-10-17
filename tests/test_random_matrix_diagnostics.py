import json
from hashlib import sha256
import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def module():
    from src.analysis import random_matrix_diagnostics
    return random_matrix_diagnostics


def test_frozen_graph_comparison_reads_exact_saved_nodes_without_refit(tmp_path):
    from src.analysis.random_matrix_search import metric_vector
    x=iid_surrogate(624,seed=11);raw=metric_vector(x)
    a=x[:104].astype(int).T@x[:104].astype(int);np.fill_diagonal(a,0)
    path=tmp_path/'structural_cache.npz'
    np.savez(path,adjacency_W104=a[None],labels_W104_K2=(np.arange(45)%2)[None],labels_W104_K3=(np.arange(45)%3)[None])
    manifest=dict(artifacts={path.name:dict(sha256=sha256(path.read_bytes()).hexdigest())},search_space=dict(endpoints=[104]))
    (tmp_path/'run_manifest.json').write_text(json.dumps(manifest))
    result=module().graph_comparison(raw,tmp_path)
    assert result['status']=='AVAILABLE_FROZEN_NO_REFIT'
    assert len(result['rows'])==1 and result['rows'][0]['end']==104
    assert result['rows'][0]['top6_overlap'] in range(7)
    assert len(result['community_rows'])==5
    assert not result['inferential']
    path.write_bytes(b'changed cache')
    assert module().graph_comparison(raw,tmp_path)['status']=='UNAVAILABLE_HASH_MISMATCH'


def test_absent_graph_is_explicitly_skipped(tmp_path):
    result=module().graph_comparison({},tmp_path)
    assert result['status']=='UNAVAILABLE_FROZEN_ARTIFACTS'
    assert result['rows']==[]


def test_plot_bundle_and_existing_outputs_are_preserved(tmp_path):
    from src.analysis.random_matrix_search import metric_vector
    raw=metric_vector(iid_surrogate(624,seed=12))
    null={k:np.repeat(raw['spectra'][None],2,axis=0) for k in ('iid','fixed_margins')}
    graph=dict(status='UNAVAILABLE_FROZEN_ARTIFACTS',rows=[],community_rows=[])
    files=module().plots(raw,null,graph,tmp_path)
    assert len(files)==10
    for name in files:
        p=tmp_path/name
        assert p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') and p.stat().st_size>1000
    with pytest.raises(FileExistsError):module().plots(raw,null,graph,tmp_path)
