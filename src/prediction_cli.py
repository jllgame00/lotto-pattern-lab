"""CLI orchestration and reproducible report exports for predictive experiments."""
from __future__ import annotations

from functools import partial
import hashlib
import importlib.util
import importlib.metadata
import json
from pathlib import Path
import platform
from time import perf_counter

import pandas as pd

from src.analysis.features import GROUPS, build_features, feature_columns
from src.backtest.ranking import evaluate, summarize_rankings
from src.collect.collector import atomic_write
from src.models.predictive import (BoostingModel, ForestModel, LogisticModel,
                                   SimilarityModel, rank_numbers, weighted_ticket)

MODELS = dict(similarity=SimilarityModel,logistic=LogisticModel,forest=ForestModel,boosting=BoostingModel)
REPORT_FILES = ['features.csv','feature_sample.csv','comparison.csv','time_blocks.csv',
                'prediction_audit.csv','feature_importance.csv','experiment.json','ablation_differences.csv']


def add_commands(commands):
    compare = commands.add_parser('compare-models',help='Experimental chronological ranking comparisons')
    compare.add_argument('--start',type=int,default=601)
    compare.add_argument('--end',type=int,help='Default penultimate draw; latest is always reserved')
    compare.add_argument('--cadence',type=int,default=26)
    compare.add_argument('--models',nargs='+',choices=list(MODELS),default=list(MODELS))
    compare.add_argument('--ablations',action='store_true',help='Also run all seven logistic feature groups')
    compare.add_argument('--reports-dir',type=Path)
    compare.add_argument('--simulations',type=int,default=2000)
    compare.add_argument('--bootstraps',type=int,default=2000)
    compare.add_argument('--tickets',type=int,default=0,help='Separate weighted tickets per target; 0 skips')
    compare.add_argument('--no-audit',action='store_true')
    predict = commands.add_parser('predict-current',help='Experimental next-draw scores; no validated advantage')
    predict.add_argument('--model',choices=list(MODELS),default='logistic')
    explain = commands.add_parser('explain-number',help='Explain same-number historical neighbors')
    explain.add_argument('number',type=int)
    for parser in (compare,predict,explain):
        parser.add_argument('--seed',type=int,default=42)
        parser.add_argument('--group',choices=list(GROUPS),default='full')
        parser.add_argument('--neighbors',type=int,default=30)
        parser.add_argument('--distance',choices=['euclidean','cityblock'],default='euclidean')
        parser.add_argument('--weighting',choices=['distance','uniform'],default='distance')


def _factory(name,args,group=None):
    extra = dict(k=args.neighbors,metric=args.distance,weighting=args.weighting) if name=='similarity' else {}
    return partial(MODELS[name],columns=feature_columns(group or args.group),seed=args.seed,**extra)


def _unavailable(name):
    if name=='forest' and not importlib.util.find_spec('sklearn'):
        return 'scikit-learn is not installed; RandomForestClassifier was not run'
    if name=='boosting' and not any(importlib.util.find_spec(p) for p in ('lightgbm','xgboost')):
        return 'LightGBM and XGBoost are not installed; no substitute was run'
    return None


def _ablation_differences(results, seed, replicates):
    """Paired incremental periodicity comparison on identical target draws."""
    import numpy as np
    base=results[results.model=='Logistic[frequency_gap]'].sort_values('target_draw')
    extended=results[results.model=='Logistic[frequency_gap_periodicity]'].sort_values('target_draw')
    if base.empty or extended.empty: return pd.DataFrame()
    n=len(base)
    delta=extended.hits.to_numpy()-base.hits.to_numpy()
    rng=np.random.default_rng(seed)
    length=min(26,n)
    starts=rng.integers(0,n,size=(replicates,int(np.ceil(n/length))))
    indices=((starts[:,:,None]+np.arange(length))%n).reshape(replicates,-1)[:,:n]
    ci=np.quantile(delta[indices].mean(axis=1),[.025,.975])
    ranking_uncertainty={}
    for metric in ('mean_winning_rank','recall_6','recall_10','recall_15'):
        differences=extended[metric].to_numpy()-base[metric].to_numpy()
        low,high=np.quantile(differences[indices].mean(axis=1),[.025,.975])
        ranking_uncertainty[f'delta_{metric}_ci_low']=float(low)
        ranking_uncertainty[f'delta_{metric}_ci_high']=float(high)
    return pd.DataFrame([dict(comparison='frequency_gap_periodicity minus frequency_gap',targets=n,
                             delta_avg_hits=float(delta.mean()),paired_ci_low=float(ci[0]),paired_ci_high=float(ci[1]),
                             delta_mean_winning_rank=float(extended.mean_winning_rank.mean()-base.mean_winning_rank.mean()),
                             **{f'delta_recall_{k}':float(extended[f'recall_{k}'].mean()-base[f'recall_{k}'].mean()) for k in (6,10,15)},
                             **ranking_uncertainty)])


def run_command(args,history,guard_outputs):
    started=perf_counter()
    if args.seed<0: raise ValueError('seed must be nonnegative')
    if args.command=='compare-models':
        root=args.reports_dir or Path(__file__).resolve().parent.parent/'reports/prediction'
        guard_outputs(args.data,*[root/name for name in REPORT_FILES])
        factories,statuses={},{}
        for name in dict.fromkeys(args.models):
            reason=_unavailable(name)
            statuses[name]=reason or 'available'
            if reason: print(f'Unavailable: {reason}',flush=True)
            else: factories[f'{MODELS[name].__name__}[{args.group}]']=_factory(name,args)
        if args.ablations:
            for group in GROUPS:
                # Full default logistic is evaluated once and reused under the ablation label.
                key=f'LogisticModel[{group}]'
                factories.pop(key,None)
                factories[f'Logistic[{group}]']=_factory('logistic',args,group)
        features=build_features(history,progress=lambda message:print(message,flush=True))
        feature_seconds=perf_counter()-started
        print(f'Feature table: {len(features):,} rows x {len(features.columns)} columns; {len(feature_columns())} predictor columns',flush=True)
        atomic_write(root/'features.csv',features.to_csv(index=False))
        atomic_write(root/'feature_sample.csv',features.head(450).to_csv(index=False))
        results,importance=evaluate(history,features,factories,start=args.start,end=args.end,
                                    cadence=args.cadence,seed=args.seed,tickets=args.tickets,audit=not args.no_audit,
                                    progress=lambda message:print(message,flush=True))
        summary=summarize_rankings(results,simulations=args.simulations,bootstraps=args.bootstraps,seed=args.seed)
        ablations=_ablation_differences(results,args.seed,args.bootstraps)
        for name,frame in [('comparison',summary['comparison']),('time_blocks',summary['time_blocks']),
                           ('prediction_audit',results),('feature_importance',importance),('ablation_differences',ablations)]:
            atomic_write(root/f'{name}.csv',frame.to_csv(index=False))
        versions={}
        for package in ('numpy','pandas','scipy','scikit-learn','lightgbm','xgboost'):
            try: versions[package]=importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError: versions[package]=None
        metadata=dict(source_path=str(args.data.resolve()),source_sha256=hashlib.sha256(args.data.read_bytes()).hexdigest(),
                      source_draws=len(history),reserved_draw=int(history.draw_no.max()),
                      feature_rows=len(features),feature_columns=len(features.columns),predictor_columns=len(feature_columns()),
                      first_feature_target=int(features.target_draw.min()),last_feature_target=int(features.target_draw.max()),
                      protocol=dict(start=args.start,end=args.end or len(history)-1,cadence=args.cadence,seed=args.seed,
                                    min_feature_history=104,tickets=args.tickets,ablations=args.ablations,tuning='none'),
                      availability=statuses,versions=dict(python=platform.python_version(),**versions),
                      model_configurations=results.attrs['model_configurations'],
                      model_runtime_seconds=results.attrs['model_runtime_seconds'],
                      runtime_seconds=round(perf_counter()-started,3),feature_seconds=round(feature_seconds,3),
                      random_simulations=summary['random_simulations'],bootstrap=summary['bootstrap'],warnings=summary['warnings'])
        atomic_write(root/'experiment.json',json.dumps(metadata,indent=2,allow_nan=False)+'\n')
        print(summary['comparison'][['model','avg_hits','rate_3_plus','rate_4_plus','best','recall_6',
                                     'recall_10','recall_15','mean_winning_rank','delta_vs_random']].to_string(index=False))
        if not ablations.empty: print(ablations.to_string(index=False))
        print(f'Runtime: {metadata["runtime_seconds"]}s; reports: {root}')
        for warning in summary['warnings']: print(f'Note: {warning}')
    else:
        name='similarity' if args.command=='explain-number' else args.model
        reason=_unavailable(name)
        if reason: raise RuntimeError(reason)
        features=build_features(history,include_current=True)
        cutoff=int(history.draw_no.max())
        training=features[features.target_draw<=cutoff].copy()
        current=features[features.target_draw==cutoff+1].drop(columns='appeared_next').copy()
        model=_factory(name,args)().fit(training,cutoff=cutoff)
        print(f'Experimental scores for draw {cutoff+1}; training cutoff {cutoff}. No validated predictive advantage.')
        if args.command=='explain-number':
            print(json.dumps(model.explain(current,args.number),indent=2,allow_nan=False))
        else:
            scores=model.score_rows(current)
            ranking=rank_numbers(scores)
            print(pd.DataFrame([dict(rank=i+1,number=n,score=scores[n]) for i,n in enumerate(ranking)]).to_string(index=False))
            print(f'Top 6: {ranking[:6]}')
            print(f'Separate weighted ticket (seed={args.seed}): {weighted_ticket(scores,seed=args.seed)}')
        print(f'Runtime: {perf_counter()-started:.2f}s')
