import json
import numpy as np
import pandas as pd
import pytest
from src.analysis.spatiotemporal import iid_surrogate


def test_pipeline_module_exists():
    import importlib.util
    assert importlib.util.find_spec('src.recurrence_cli') is not None


def test_development_never_accepts_later_history():
    from src.backtest.recurrence import development_search
    with pytest.raises(ValueError,match='900'):
        development_search(iid_surrogate(901,seed=1))


def test_batched_scores_match_single_target_model():
    from src.models.recurrence import RecurrenceContinuationModel, trajectory_distances, successor_scores
    from src.analysis.recurrence import EmbeddingConfig,observations,embed,fit_scaler
    x=iid_surrogate(200,seed=2);c=EmbeddingConfig('C',10,3,2,'euclidean')
    o=observations(x,c);scaler=fit_scaler(o,150);e,ends=embed(o[:180],c,scaler)
    d,candidates=trajectory_distances(e,ends,c,[160,170,180],3)
    scores=successor_scores(x[:180],candidates,d,5,'inverse')
    model=RecurrenceContinuationModel(c,k=5,weighting='inverse',length=3).fit(x[:150],cutoff=150)
    for i,endpoint in enumerate([160,170,180]):
        np.testing.assert_allclose(scores[i],list(model.score_matrix(x[:endpoint],target=endpoint+1).values()))


def test_tiny_walk_forward_matches_targets_and_cutoffs():
    from src.backtest.translation import walk_forward
    from src.models.recurrence import RecurrenceAnalogModel
    x=iid_surrogate(150,seed=8)
    data=pd.DataFrame([dict(draw_no=i+1,draw_date=pd.Timestamp('2002-12-07')+pd.Timedelta(weeks=i),
        **dict(zip([f'num{k}' for k in range(1,7)],np.flatnonzero(row)+1)),
        bonus=int(np.flatnonzero(~row)[0]+1)) for i,row in enumerate(x)])
    rows=walk_forward(data,{'RecurrenceAnalogModel':RecurrenceAnalogModel},start=140,end=150,combined=False)
    assert rows.groupby('model').size().tolist()==[11,11]
    assert (rows.feature_cutoff==rows.target_draw-1).all()
    assert (rows.training_cutoff<rows.target_draw).all()


def test_fixed_margin_rebuild_preserves_margins():
    from src.analysis.spatiotemporal import constrained_surrogate
    from src.analysis.recurrence import observations,EmbeddingConfig
    x=iid_surrogate(200,seed=9);s=constrained_surrogate(x,seed=10)
    np.testing.assert_array_equal(x.sum(0),s.sum(0)); assert np.all(s.sum(1)==6)
    c=EmbeddingConfig('C',26,2,1,'cosine')
    assert not np.allclose(observations(x,c)[25:],observations(s,c)[25:])


def test_binary_distance_algebra_matches_scipy():
    from scipy.spatial.distance import cdist
    from src.analysis.recurrence import distances
    a=iid_surrogate(30,seed=1).astype(float);b=iid_surrogate(20,seed=2).astype(float)
    for metric in ('hamming','jaccard'):
        np.testing.assert_allclose(distances(a,b,metric),cdist(a,b,metric))


def test_restored_archive_must_include_all_prior_phases(tmp_path):
    from src.phase11_freeze import prepare_freeze
    archive=tmp_path/'archive';archive.mkdir();(archive/'arbitrary.txt').write_text('x')
    with pytest.raises(ValueError,match='complete prior'):
        prepare_freeze(tmp_path/'selection.json',archive,protected={'arbitrary.txt':'bad'})


def test_cli_loader_rejects_suffix_before_parsing(tmp_path):
    from src.recurrence_cli import load_research_source
    root=__import__('pathlib').Path(__file__).resolve().parents[1]
    raw=(root/'data/raw/lotto_history.csv').read_bytes()
    path=tmp_path/'future.csv'
    path.write_bytes(raw+b'INVALID_FUTURE_SUFFIX_MUST_NOT_BE_PARSED\n')
    with pytest.raises(ValueError,match='suffix'):
        load_research_source(path)


def test_parallel_null_same_as_serial():
    from src.analysis.recurrence_search import null_search
    x=iid_surrogate(300,seed=17)
    kwargs=dict(replicates=1,seed=31,search_args=dict(start=140,end=299,scale_end=130))
    assert null_search(x,workers=2,**kwargs)==null_search(x,workers=1,**kwargs)


def test_sparse_archive_inventory_cannot_claim_ready(tmp_path):
    from hashlib import sha256
    from src.phase11_freeze import prepare_freeze
    archive=tmp_path/'archive';archive.mkdir();protected={}
    for name in ['x.txt',*[f'phase{p}/x.txt' for p in range(6,11)]]:
        file=archive/name;file.parent.mkdir(exist_ok=True);file.write_bytes(b'x')
        protected[name]=sha256(b'x').hexdigest()
    with pytest.raises(ValueError,match='complete prior'):
        prepare_freeze(tmp_path/'selection.json',archive,protected=protected)


def test_refused_null_rerun_preserves_existing_evidence(tmp_path):
    from src.recurrence_cli import analyze
    for name in ('real_search.csv','real_maxima.json','null_progress.jsonl'):
        (tmp_path/name).write_bytes(b'original evidence')
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    with pytest.raises(ValueError,match='Existing null'):
        analyze(iid_surrogate(900,seed=1),tmp_path,1,workers=1)
    assert before=={p.name:p.read_bytes() for p in tmp_path.iterdir()}


def test_historical_example_matches_evaluation_fit():
    from src.recurrence_cli import historical_example
    from src.models.recurrence import RecurrenceAnalogModel
    from src.analysis.recurrence import EmbeddingConfig
    x=iid_surrogate(200,seed=4)
    s={'models':{'RecurrenceAnalogModel':dict(model='RecurrenceAnalogModel',
        embedding=dict(family='B',window=1,m=2,tau=1,metric='euclidean'),k=5,weighting='inverse',length=1)}}
    model=RecurrenceAnalogModel(EmbeddingConfig('B',1,2,1,'euclidean'),k=5,weighting='inverse').fit(x[:178],cutoff=178)
    scores=model.score_matrix(x[:199],target=200)
    from src.models.predictive import rank_numbers
    row=pd.Series(dict(target_draw=200,training_cutoff=178,scores=json.dumps(scores),ranking=json.dumps(rank_numbers(scores))))
    example=historical_example(x,s,row)
    assert example['training_cutoff']==178
    assert example['ranking']==rank_numbers(scores)


def test_development_summary_keeps_window_and_period_separate():
    from src.backtest.recurrence import summarize_development
    models=['NearestSuccessorBaseline','RecurrenceAnalogModel','RecurrenceContinuationModel']
    rows=pd.DataFrame([dict(candidate=m,model=m,mean_hits=.8,early_dev=.7,late_dev=.9) for m in models])
    configs={m:dict(model=m,embedding=dict(family='C',window=26,m=2,tau=1,metric='cosine'),k=5) for m in models}
    selected,stability=summarize_development(rows,configs)
    assert set(selected)==set(models)
    assert set(stability.period)=={'mean_hits','early_dev','late_dev'}
    assert set(stability.window)=={26}
