import numpy as np
import pytest


def panel(start=901,end=1015):
    rng=np.random.default_rng(11)
    ranks=np.array([[rng.permutation(45)+1 for _ in range(4)] for _ in range(end-start+1)])
    actual=np.zeros((len(ranks),45),bool);actual[:,:6]=True
    return dict(targets=np.arange(start,end+1),ranks=ranks,actual=actual,names=['GapLogistic','GraphStructureModel','GapShapeModel','MirrorModel'])


def test_rank_average_and_exact_ties_smaller_number_first():
    from src.analysis.final_ensemble import combine_ranks
    r=np.array([[np.arange(1,46),np.arange(45,0,-1)]])
    np.testing.assert_array_equal(combine_ranks(r,[.5,.5])[0],np.arange(1,46))
    np.testing.assert_array_equal(combine_ranks(r,[1,0])[0],r[0,0])
    with pytest.raises(ValueError):combine_ranks(r,[-1,2])


def test_templates_have_exact_small_convex_search():
    from src.analysis.final_ensemble import templates
    t=templates(panel()['names'])
    assert len(t)==47 and sum(v['equal'] for v in t)==11
    assert len({tuple(v['weights']) for v in t})==47
    assert all(sum(v['weights'])==pytest.approx(1) and 2<=v['size']<=4 for v in t)


def test_split_rejects_future_and_has_disjoint_exact_blocks():
    from src.analysis.final_ensemble import split_panel
    p=panel(901,1245)
    a,b,c=[split_panel(p,s) for s in ('development','validation','final')]
    assert [len(v['targets']) for v in (a,b,c)]==[115]*3
    assert a['targets'][-1]<b['targets'][0] and b['targets'][-1]<c['targets'][0]
    p['targets'][-1]=1246
    with pytest.raises(ValueError):split_panel(p,'development')


def test_development_selection_rejects_validation_and_ignores_unseen_final():
    from src.analysis.final_ensemble import select_development,split_panel
    p=panel(901,1245);d=split_panel(p,'development')
    one=select_development(d)
    p['actual'][230:]=np.roll(p['actual'][230:],20,axis=1)
    two=select_development(split_panel(p,'development'))
    assert one['winner']==two['winner'] and one['best_single']==two['best_single']
    with pytest.raises(ValueError):select_development(p)


def test_validation_gate_requires_both_primary_and_top6_support():
    from src.analysis.final_ensemble import validation_support
    refs=[dict(mean_winning_rank=21.,avg_top6=.8)]
    assert validation_support(dict(mean_winning_rank=20.,avg_top6=.8),refs)
    assert not validation_support(dict(mean_winning_rank=20.,avg_top6=.7),refs)
    assert not validation_support(dict(mean_winning_rank=21.,avg_top6=.9),refs)


def test_metrics_and_diversity_known_identity_and_reverse():
    from src.analysis.final_ensemble import metrics,diversity
    p=panel();p['ranks'][:,0]=np.arange(1,46);p['ranks'][:,1]=np.arange(45,0,-1)
    m=metrics(p['ranks'][:,0],p['actual'])
    assert m['avg_top6']==6 and m['mean_winning_rank']==3.5 and m['all6_pool15']==115
    v=diversity(p)
    pair=next(x for x in v if x['left']==p['names'][0] and x['right']==p['names'][1])
    assert pair['spearman']==pytest.approx(-1) and pair['top6_overlap']==0


def test_bootstrap_paired_sign_and_simultaneous_intervals():
    from src.analysis.final_ensemble import paired_interval
    a=np.ones(115);b=np.zeros(115)
    r=paired_interval(a,b,seed=8,replicates=200)
    assert r['difference']==r['ci_low']==r['simultaneous_low']==1
    assert r==paired_interval(a,b,seed=8,replicates=200)
    with pytest.raises(ValueError):paired_interval(a,b[:-1])


def test_leaveout_is_frozen_reweighting_and_correlation():
    from src.analysis.final_ensemble import leave_one_out
    p=panel(1131,1245);r=leave_one_out(p,[.25]*4)
    assert len(r)==4 and all('top6_change' in row and 'spearman_with_full' in row for row in r)


def test_placebos_repeat_and_preserve_candidate_diversity():
    from src.analysis.final_ensemble import placebo_panel,diversity,random_weight_templates
    p=panel(901,1245)
    a=placebo_panel(p,seed=9);b=placebo_panel(p,seed=9)
    np.testing.assert_array_equal(a['ranks'],b['ranks'])
    np.testing.assert_array_equal(a['actual'],p['actual'])
    assert not np.array_equal(a['ranks'],p['ranks'])
    for one,two in zip(diversity(a),diversity(p)):
        assert one['spearman']==pytest.approx(two['spearman'])
        assert one['top6_overlap']==two['top6_overlap']
    t=random_weight_templates(p['names'],seed=10)
    assert len(t)==47 and t==random_weight_templates(p['names'],seed=10)


def test_failed_validation_falls_back_without_selecting_runnerup():
    from src.analysis.final_ensemble import select_development,validate_selection
    d=panel();selection=select_development(d)
    v=panel(1016,1130);v['ranks'][:]=np.arange(1,46)
    gate=validate_selection(v,selection)
    assert not gate['passed'] and gate['selected']['id']=='equal_all'
    assert gate['development_winner']['id']==selection['winner']['id']


def test_placebo_selection_never_uses_final_labels_and_all_replicates_retained():
    from src.analysis.final_ensemble import run_placebos
    p=panel(901,1245);one=run_placebos(p,replicates=2)
    p['actual'][230:]=np.roll(p['actual'][230:],23,axis=1)
    two=run_placebos(p,replicates=2)
    assert len(one)==len(two)==4
    for a,b in zip(one,two):
        for key in ('kind','replicate','seed','gate_passed','winner','selected_weights','best_single','development_rank_gain','validation_rank_gain'):
            assert a[key]==b[key]
        if not a['gate_passed']:assert a['final_promoted_gain']==0
