import json
from hashlib import sha256
import numpy as np
import pandas as pd
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def module():
    from src.analysis import topology_diagnostics
    return topology_diagnostics


def test_topological_states_compare_only_equal_config_window_and_point_counts():
    from src.analysis.topology_search import metric_vector
    raw=metric_vector(iid_surrogate(416,seed=23));result=module().topological_states(raw)
    assert result['descriptive_only'] and result['pairs']
    counts={'A_jaccard':208,'A_hamming':208,'B_euclidean':208,'C26_euclidean':8,'C52_euclidean':4}
    assert all(a['points']==counts[a['config']] for a in result['pairs'])
    assert all(len(a['features'])==4 for a in result['states'])
    first=next(c for c in raw['clouds'] if c['location']=='rolling' and c['window']==208)
    first['points']=999
    with pytest.raises(ValueError,match='point'):module().topological_states(raw)


def test_frozen_graph_rmt_comparison_hashes_and_no_refit(tmp_path):
    from src.analysis.topology_search import metric_vector
    raw=metric_vector(iid_surrogate(416,seed=24))
    rmt=tmp_path/'reports/random_matrix';graph=tmp_path/'reports/graph_hypergraph'
    rmt.mkdir(parents=True);graph.mkdir(parents=True)
    a=rmt/'interval_summary.csv';b=graph/'graph_rows.csv'
    pd.DataFrame([dict(location='rolling',kind='correlation',window=208,end=e,largest=i+1,effective_rank=44-i) for i,e in enumerate((208,312,416))]).to_csv(a,index=False)
    pd.DataFrame([dict(W=104,end=e,concentration=.1*(i+1)) for i,e in enumerate((208,312,416))]).to_csv(b,index=False)
    (rmt/'manifest.json').write_text(json.dumps(dict(artifacts={a.name:sha256(a.read_bytes()).hexdigest()})))
    (graph/'run_manifest.json').write_text(json.dumps(dict(artifacts={b.name:dict(sha256=sha256(b.read_bytes()).hexdigest())})))
    result=module().frozen_comparison(raw,tmp_path)
    assert result['status']=='AVAILABLE_FROZEN_NO_REFIT' and not result['refitted']
    assert len(result['rmt_rows'])==3 and len(result['graph_rows'])==3
    assert all(r['graph_window']==104 and r['topology_window']==208 for r in result['graph_rows'])
    a.write_text('changed')
    assert module().frozen_comparison(raw,tmp_path)['rmt_status']=='HASH_MISMATCH'


def test_missing_old_outputs_are_explicitly_skipped(tmp_path):
    result=module().frozen_comparison({},tmp_path)
    assert result['rmt_rows']==result['graph_rows']==[]
    assert result['status']=='UNAVAILABLE_FROZEN_ARTIFACTS'


def test_h0_plot_bundle_and_overwrite_protection(tmp_path):
    from src.analysis.topology_search import metric_vector
    raw=metric_vector(iid_surrogate(416,seed=25))
    c=dict(draws=416,keys=raw['keys'],mean=np.zeros(len(raw['keys'])),std=np.ones(len(raw['keys'])),eligible=np.ones(len(raw['keys']),bool))
    null=np.tile(raw['values'],(4,1));relations=dict(rmt_rows=[],graph_rows=[])
    names=module().plots(raw,c,null,relations,tmp_path)
    assert len(names)>=8 and not any('h1' in name for name in names)
    for name in names:
        p=tmp_path/name;assert p.stat().st_size>1000 and p.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    with pytest.raises(FileExistsError):module().plots(raw,c,null,relations,tmp_path)
