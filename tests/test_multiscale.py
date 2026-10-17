"""Phase 12 contracts: cutoff, identical search rights, and global inference."""
import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.analysis.multiscale import representations, complete_search, null_search, compare_maxima


def test_binary_representation_exact_causal_cutoff():
    x=iid_surrogate(240,seed=12)
    names,y=representations(x,cutoff=240)
    assert y.shape==(240,53)
    assert np.array_equal(y[:,:45],x)
    assert names[:2]==['number_1','number_2']
    with pytest.raises(ValueError): representations(x,cutoff=239)
    with pytest.raises(ValueError): representations(iid_surrogate(1246,seed=1),cutoff=1246)


def test_complete_search_global_max_and_parity():
    x=iid_surrogate(240,seed=1)
    args=dict(periods=(8,13,26),lengths=(26,),endpoints=(240,),window=208)
    real=complete_search(x,**args)
    rows=null_search(x,replicates=2,seed=120042,search_args=args)
    assert len(rows)==4
    assert all(r['space']==real['space'] for r in rows)
    assert len({r['representation_hash'] for r in rows})==4
    assert all(r['rebuilt'] for r in rows)
    assert real['maxima']['wavelet_peak']==max(r['wavelet_peak'] for r in real['wavelet_rows'])
    assert rows==null_search(x,replicates=2,seed=120042,search_args=args)
    compared=compare_maxima(real,rows)
    assert len(compared)==12
    assert all(r['adjusted_p']==min(1,6*r['global_p']) for r in compared)


def test_empirical_max_uses_plus_one_and_ties():
    from src.analysis.multiscale import FAMILIES
    real={'maxima':dict.fromkeys(FAMILIES,2.)}
    rows=[dict(null_model=k,**dict.fromkeys(FAMILIES,v)) for k in ('iid','fixed_margins') for v in (1.,2.,3.)]
    assert all(r['global_p']==.75 for r in compare_maxima(real,rows))


def test_constant_history_has_explicit_zero_leaders():
    x=np.zeros((240,45),bool);x[:,:6]=True
    r=complete_search(x,periods=(8,13,26),lengths=(26,),endpoints=(240,),window=208)
    assert set(r['leaders'])==set(r['maxima'])
    assert all(v==0 for v in r['maxima'].values())
    assert r['regions']==[]


def test_noninteger_constant_series_has_no_roundoff_structure():
    from src.analysis.wavelet import morlet_transform
    from src.analysis.ssa import decompose
    values=np.full(240,10/3)
    assert not morlet_transform(values,periods=(8,26))['power'].any()
    assert not decompose(values,26)['energy_ratios'].any()
