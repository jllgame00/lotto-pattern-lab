import numpy as np
import pytest
from src.analysis.spatiotemporal import iid_surrogate
from src.analysis.complexity_search import metric_vector,fit_calibration,standardize,complete_search,null_search,compare_maxima,FAMILIES


def test_exact_complete_search_space_and_no_future():
    x=iid_surrogate(1245,seed=160);r=metric_vector(x)
    assert r['space']['cells']==5184 and r['space']['rolling_windows']==32
    assert r['space']['families']==dict(entropy=1675,conditional=1532,ordinal=136,lz=1489,compression=191,chronological=161)
    assert len(set(r['keys']))==5184
    assert metric_vector(x[:900])['space']['cells']==3942
    with pytest.raises(ValueError):metric_vector(iid_surrogate(1246,seed=10))


def test_independent_calibration_complete_null_determinism():
    x=iid_surrogate(104,seed=66);c=fit_calibration(104,replicates=3,seed=21)
    r=metric_vector(x);z=standardize(r,c)
    assert len(z)==len(r['keys']) and np.isfinite(z).any()
    a=null_search(x,{104:c},replicates=1,seed=22,include_development=False)
    b=null_search(x,{104:c},replicates=1,seed=22,include_development=False,workers=2)
    assert len(a)==len(b)==3
    for aa,bb in zip(a,b):
        assert aa['null_model']==bb['null_model']
        assert aa['full']['representation_hash']==bb['full']['representation_hash']
        assert aa['full']['space']==r['space']
        assert aa['full']['maxima']==bb['full']['maxima']
    real=complete_search(r,c);p=compare_maxima(real,a,scope='full')
    assert len(p)==18 and set(q['null_model'] for q in p)=={'iid','fixed_margins','draw_shuffle'}
    for q in p:
        values=[row['full']['maxima'][q['family']] for row in a if row['null_model']==q['null_model']]
        expected=(1+sum(v>=real['maxima'][q['family']] for v in values))/2
        assert q['global_p']==expected and q['adjusted_p']==min(1,6*expected)


def test_calibration_integrity_and_unsupported_cells():
    c=dict(keys=['a','b'],mean=np.array([0.,10.]),std=np.array([1.,0.]),eligible=np.array([True,False]))
    z=standardize(dict(keys=['a','b'],values=np.array([3.,1000.])),c)
    assert z[0]==3 and np.isnan(z[1])
    with pytest.raises(ValueError):standardize(dict(keys=['b','a'],values=np.array([1.,2.])),c)
    with pytest.raises(ValueError):null_search(iid_surrogate(104,seed=1),{},replicates=0)


def test_inner_three_shuffle_statistic_uses_history_hash_seeds():
    from hashlib import sha256
    from src.analysis.complexity_encoding import lz78
    x=iid_surrogate(104,seed=97);raw=metric_vector(x)
    i=next(i for i,m in enumerate(raw['metadata']) if m['scope']=='chronological' and m['representation']=='number01' and m['kind']=='lz78')
    digest=int(sha256(x.tobytes()).hexdigest()[:8],16);references=[]
    for j in range(3):
        child=int(np.random.SeedSequence([160003,digest,j]).generate_state(1)[0])
        order=np.random.default_rng(child).permutation(len(x))
        references.append(lz78(x[order,0],2)['normalized'])
    expected=np.mean(references)-lz78(x[:,0],2)['normalized']
    assert raw['values'][i]==pytest.approx(expected)


def test_development_fixed_margin_generator_receives_exact_prefix900(monkeypatch):
    import src.analysis.complexity_search as module
    x=iid_surrogate(1245,seed=98);calibrations={};captured=[]
    for n in (1245,900):
        raw=metric_vector(x[:n],details=False);size=len(raw['keys'])
        calibrations[n]=dict(keys=raw['keys'],mean=np.zeros(size),std=np.ones(size),eligible=np.ones(size,dtype=bool))
    original=module.constrained_surrogate
    def traced(values,**kwargs):
        captured.append(values.copy());return original(values,**kwargs)
    monkeypatch.setattr(module,'constrained_surrogate',traced)
    result=module._null_job((x,'fixed_margins',1,0,99,calibrations,True))
    assert len(captured)==2 and np.array_equal(captured[0],x)
    assert np.array_equal(captured[1],x[:900])
    assert result['development']['draws']==900
