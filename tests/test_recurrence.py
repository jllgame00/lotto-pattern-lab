import numpy as np
import pytest

from src.analysis.spatiotemporal import iid_surrogate


def test_recurrence_module_exists():
    import importlib.util
    assert importlib.util.find_spec('src.analysis.recurrence') is not None


def test_embedding_indices_and_dimensions():
    from src.analysis.recurrence import EmbeddingConfig, observations, embed
    x = iid_surrogate(100, seed=2)
    for family, w, width in [('A', 1, 45), ('B', 1, 13), ('C', 10, 45)]:
        c = EmbeddingConfig(family, w, 3, 4, 'hamming' if family == 'A' else 'euclidean')
        o = observations(x, c)
        e, ends = embed(o, c)
        assert e.shape == (100 - c.span, 3 * width)
        np.testing.assert_array_equal(e[-1], np.concatenate([o[99], o[95], o[91]]))
        assert ends[0] == c.span + 1 and ends[-1] == 100
    assert np.all(observations(x, EmbeddingConfig()).sum(axis=1) == 6)


@pytest.mark.parametrize('w', [10, 26, 52])
def test_rolling_causal(w):
    from src.analysis.recurrence import EmbeddingConfig, observations
    x = iid_surrogate(100, seed=3)
    c = EmbeddingConfig('C', w, 2, 1, 'cosine')
    o = observations(x, c)
    np.testing.assert_allclose(o[79], x[80-w:80].mean(axis=0))
    np.testing.assert_array_equal(o[:80], observations(x[:80], c))


def test_shape_and_insufficient_history():
    from src.analysis.recurrence import EmbeddingConfig, observations, embed
    x = np.zeros((5, 45)); x[:, :6] = 1
    c = EmbeddingConfig('B', 1, 2, 1, 'euclidean')
    o = observations(x, c)
    np.testing.assert_allclose(o[0], [21, 3.5, np.std(np.arange(1,7)), 1, 6, 5, 1, 0, 1, 1, 5, 3, 6])
    with pytest.raises(ValueError, match='history'):
        embed(observations(x, EmbeddingConfig(m=4, tau=26)), EmbeddingConfig(m=4, tau=26))


def test_distances_and_training_scaler():
    from src.analysis.recurrence import distances, fit_scaler
    a = np.array([[1.,0,1], [0,1,1]])
    assert distances(a, a, 'hamming')[0,1] == pytest.approx(2/3)
    assert distances(a, a, 'jaccard')[0,1] == pytest.approx(2/3)
    zero = np.zeros((1,3))
    assert distances(zero,zero,'cosine')[0,0] == 0
    assert distances(zero,a,'cosine')[0,0] == 1
    mean, scale = fit_scaler(np.array([[1.,2], [3,6], [999,999]]), 2)
    np.testing.assert_allclose(mean,[2,4]); np.testing.assert_allclose(scale,[1,2])
    assert distances(np.array([[0.,0]]), np.array([[3.,4]]),'euclidean')[0,0] == 5


def test_theiler_and_successor_exclusion():
    from src.analysis.recurrence import EmbeddingConfig, eligible
    c = EmbeddingConfig('C', 10, 3, 4, 'cosine')
    assert c.span == 17
    mask = eligible(np.array([40, 58, 59]), c)
    assert not mask[0,1] and mask[0,2] and not np.diag(mask).any()
    assert not eligible(np.array([40,59]), c, length=2)[0,1]


def test_recurrence_constructions():
    from src.analysis.recurrence import recurrence_matrix
    d = np.abs(np.arange(10)[:,None] - np.arange(10)[None,:]).astype(float)
    valid = d > 2
    r = recurrence_matrix(d, valid, 'density', density=.2)
    assert np.array_equal(r,r.T) and not r[~valid].any()
    assert r.sum() == 2 * int(valid.sum()/2*.2)
    r = recurrence_matrix(d,valid,'knn',k=1)
    assert r.any() and np.array_equal(r,r.T) and not r[~valid].any()


def test_rqa_known_lines_and_sparse():
    from src.analysis.recurrence import rqa
    r = np.zeros((7,7),bool); r[0,3]=r[1,4]=r[2,5]=True
    q = rqa(r)
    assert q['det'] == 1 and q['lmax'] == 3 and q['mean_diagonal'] == 3
    r = np.zeros((7,7),bool); r[1:4,5] = True
    q = rqa(r)
    assert q['laminarity'] == 1 and q['trapping_time'] == 3
    r = np.zeros((7,7),bool); r[0,[1,3,6]] = True
    q = rqa(r)
    assert q['recurrence_time_mean'] == 2.5
    assert rqa(np.zeros((4,4),bool))['det'] == 0


def test_cutoff_refuses_1246():
    from src.analysis.recurrence import research_matrix
    with pytest.raises(ValueError, match='1245'):
        research_matrix(iid_surrogate(1246, seed=1))


@pytest.mark.parametrize('name', ['NearestSuccessorBaseline','RecurrenceAnalogModel','RecurrenceContinuationModel'])
def test_models_causal_alignment_and_future_refusal(name):
    from src.models import recurrence as models
    from src.analysis.recurrence import EmbeddingConfig
    x = iid_surrogate(180, seed=4)
    model = getattr(models,name)(EmbeddingConfig()).fit(x[:130],cutoff=130)
    scores = model.score_matrix(x[:160],target=161)
    assert set(scores) == set(range(1,46))
    audit = model.analogs(x[:160],target=161)
    assert all(r['successor_draw'] == r['endpoint']+1 for r in audit)
    assert all(r['successor_draw'] < 160-model.config.span-model.length+1 for r in audit)
    assert all(r['successor_numbers'] == (np.flatnonzero(x[r['endpoint']])+1).tolist() for r in audit)
    with pytest.raises(ValueError): model.score_matrix(x[:161],target=161)
    with pytest.raises(ValueError): model.score_matrix(x[:160],target=162)
    bad=x[:160].copy(); bad[0]=x[170]
    with pytest.raises(ValueError): model.score_matrix(bad,target=161)


def test_planted_recurrence_recovers_successor():
    from src.models.recurrence import NearestSuccessorBaseline
    from src.analysis.recurrence import EmbeddingConfig
    block = iid_surrogate(15,seed=6)
    x = np.tile(block,(10,1))
    model = NearestSuccessorBaseline(EmbeddingConfig()).fit(x[:140],cutoff=140)
    scores = model.score_matrix(x[:149],target=150)
    assert set(n for n,v in scores.items() if v) == set(np.flatnonzero(x[149])+1)


def test_successor_diagnostic_and_rank_ties():
    from src.analysis.recurrence import successor_diagnostic, rank_correlation
    x = iid_surrogate(20,seed=7); x[8] = x[3]
    ends = np.array([3,8,15]); d=np.array([[0,0,1],[0,0,1],[1,1,0]])
    q = successor_diagnostic(x,ends,d,~np.eye(3,dtype=bool),details=True)
    assert q['spearman'] < 0 and q['nearest_overlap'] >= 3
    assert rank_correlation([1,1,2],[1,1,2]) == pytest.approx(1)
    assert rank_correlation([1,1],[2,3]) == 0


def test_full_search_parity_and_determinism():
    from src.analysis.recurrence_search import complete_search, null_search, SEARCH_SPACE
    x = iid_surrogate(300,seed=1)
    args = dict(start=140,end=299,scale_end=130)
    real = complete_search(x,**args)
    assert len(real['rows']) == 360 and real['space'] == SEARCH_SPACE
    one = null_search(x,replicates=1,seed=12,search_args=args)
    two = null_search(x,replicates=1,seed=12,search_args=args)
    assert one == two
    assert len(one)==2 and all(r['configurations']==180 and r['rebuilt'] for r in one)
    assert any(r['observation_hash'] != real['observation_hash'] for r in one)


def test_selection_rejects_later_targets_and_unequal_targets():
    import pandas as pd
    from src.backtest.recurrence import select_development
    rows=pd.DataFrame([dict(candidate='a',target_draw=900,hits=0),dict(candidate='b',target_draw=900,hits=1)])
    assert select_development(rows)=='b'
    rows.loc[0,'target_draw']=901
    with pytest.raises(ValueError): select_development(rows)


def test_prospective_requires_archive_and_refuses_1246(tmp_path):
    from src.phase11_freeze import prepare_freeze
    with pytest.raises(ValueError,match='1247'):
        prepare_freeze(tmp_path/'selection.json',tmp_path/'missing',target=1246)
    with pytest.raises(ValueError,match='PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION'):
        prepare_freeze(tmp_path/'selection.json',tmp_path/'missing',target=1247)
    assert not list(tmp_path.iterdir())


def test_historical_models_reject_target_1246():
    from src.models.recurrence import RecurrenceAnalogModel
    x=iid_surrogate(1245,seed=91)  # Synthetic data, no real draw1246 observation.
    model=RecurrenceAnalogModel().fit(x[:900],cutoff=900)
    with pytest.raises(ValueError,match='1245'):
        model.score_matrix(x,target=1246)


def test_diagonal_entropy_and_all_declared_dimensions():
    from src.analysis.recurrence import rqa,configurations
    r=np.zeros((9,9),bool)
    r[[0,1,4,5,6],[4,5,1,2,3]]=True
    q=rqa(r)
    assert q['diagonal_entropy']==pytest.approx(np.log(2))
    assert q['mean_diagonal']==2.5 and q['det']==1
    configs=configurations()
    assert len(configs)==180
    assert {c.dimension for c in configs if c.family=='B'}=={26,39,52}
    assert {c.dimension for c in configs if c.family in ('A','C')}=={90,135,180}
