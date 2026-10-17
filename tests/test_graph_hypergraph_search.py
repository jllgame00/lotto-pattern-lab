import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.analysis.graph_hypergraph_search import complete_search,null_search,compare_maxima,FAMILIES


def test_full_search_parity_own_maxima_and_determinism():
    x=iid_surrogate(240,seed=14);args=dict(endpoints=(104,156,208,239),windows=(26,52),communities=(2,))
    real=complete_search(x,**args)
    rows=null_search(x,replicates=2,seed=140042,search_args=args)
    assert len(rows)==4 and all(row['space']==real['space'] for row in rows)
    assert len({row['representation_hash'] for row in rows})==4
    assert rows==null_search(x,replicates=2,seed=140042,search_args=args)
    assert real['maxima']['edge']==max(r['edge_score'] for r in real['graph_rows'])
    assert real['maxima']['triple']==max(r['triple_score'] for r in real['graph_rows'])
    assert real['space']['graphs']==8
    assert real['space']['pair_cells']==8*990
    assert real['space']['triple_cells']==8*14190


def test_maximum_plus_one_ties_and_five_family_correction():
    real={'maxima':dict.fromkeys(FAMILIES,2.)}
    rows=[dict(null_model=k,**dict.fromkeys(FAMILIES,v)) for k in ('iid','fixed_margins') for v in (1.,2.,3.)]
    compared=compare_maxima(real,rows)
    assert len(compared)==10 and all(r['global_p']==.75 and r['adjusted_p']==1 for r in compared)


def test_successor_never_uses1246_and_requires_nonoverlap():
    with pytest.raises(ValueError):complete_search(iid_surrogate(1246,seed=2))
    with pytest.raises(ValueError):complete_search(iid_surrogate(240,seed=2),endpoints=(104,240))
    r=complete_search(iid_surrogate(240,seed=3),endpoints=(104,130,156,239),windows=(26,),communities=(2,))
    assert all(row['second_end']-row['first_end']>=row['W'] for row in r['persistence_rows'])
    assert all(row['target_draw']<=240 and row['target_draw']==row['endpoint']+1 for row in r['successor_rows'])
