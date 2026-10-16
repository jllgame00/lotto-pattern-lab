"""Fixed gap robustness and prize-aware experiment orchestration."""
from functools import partial
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from src.analysis.features import GAP, PERIODICITY, build_features, feature_columns
from src.backtest.prize_experiment import evaluate_portfolios
from src.backtest.prize_reports import candidate_reports, paired_difference, portfolio_reports, random_portfolio_reference
from src.backtest.prizes import exact_ticket_prizes
from src.backtest.ranking import evaluate, summarize_rankings
from src.collect.collector import atomic_write
from src.models.gap_research import GapHeuristic, HEURISTICS, coefficient_audit, ranking_contributions
from src.models.predictive import LogisticModel, SimilarityModel, ForestModel, BoostingModel
from src.research_seal import LAST_OPEN_DRAW, prefix_hash

FILES = ['experiment.json','coefficient_audit.csv','coefficient_stability.csv','ranking_contributions.csv',
         'ranking_comparisons.csv','ranking_time_blocks.csv','ranking_audit.csv','gap_vs_heuristics.csv',
         'gap_periodicity_comparison.csv','candidate_pools.csv','candidate_summary.csv','candidate_time_blocks.csv',
         'pool_5plus_events.csv','portfolio_draws.csv','portfolio_summary.csv','portfolio_replicates.csv',
         'portfolio_time_blocks.csv','prize_events.csv','comparison.csv','feature_sample.csv','dependency_status.json']
FILES.append('uniform_portfolio_reference.csv')


def add_command(commands):
    parser=commands.add_parser('prize-eval',help='Sealed-prefix gap robustness and fixed-budget prize research')
    parser.add_argument('--starts',type=int,nargs='+',default=[401,501,601,701,801])
    parser.add_argument('--primary-start',type=int,default=601)
    parser.add_argument('--end',type=int,default=1244)
    parser.add_argument('--cadence',type=int,default=26)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--pool-size',type=int,choices=[8,10,12,15],default=12)
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--bootstraps',type=int,default=2000)
    parser.add_argument('--simulations',type=int,default=2000)
    parser.add_argument('--reports-dir',type=Path)
    parser.add_argument('--core-only',action='store_true',help='Skip legacy full/similarity/other ablations; keep gap and heuristics')


def dependencies():
    packages={name:bool(importlib.util.find_spec(module)) for name,module in
              [('scikit-learn','sklearn'),('LightGBM','lightgbm'),('XGBoost','xgboost')]}
    return dict(installed=packages,PIP_NO_INDEX=os.environ.get('PIP_NO_INDEX'),
                diagnosis='PIP_NO_INDEX=1 prevents package index lookup' if os.environ.get('PIP_NO_INDEX')=='1' else 'See installed status',
                substitutes='No tree-model replacement implemented',
                network_probe='Not repeated automatically; previous PyPI HTTPS probe failed with WinError10061')


def _factories(seed,extra=False):
    models={'GapLogistic':partial(LogisticModel,columns=GAP,seed=seed),
            'GapPeriodicityLogistic':partial(LogisticModel,columns=GAP+PERIODICITY,seed=seed)}
    models.update({f'GapRule[{rule}]':partial(GapHeuristic,method=rule,seed=seed) for rule in HEURISTICS})
    if extra:
        for group in ('full','frequency','periodicity','calendar','frequency_gap','frequency_gap_periodicity'):
            models[f'Logistic[{group}]']=partial(LogisticModel,columns=feature_columns(group),seed=seed)
        models['SimilarityModel']=partial(SimilarityModel,seed=seed)
        if importlib.util.find_spec('sklearn'): models['RandomForest']=partial(ForestModel,seed=seed)
        if any(importlib.util.find_spec(name) for name in ('lightgbm','xgboost')):
            models['Boosting']=partial(BoostingModel,seed=seed)
    return models


def _stability(audits):
    records=[]
    for (start,model,feature),group in audits.groupby(['evaluation_start','model','feature']):
        group=group.sort_values('training_cutoff')
        signs=group.sign.to_numpy()
        records.append(dict(evaluation_start=start,model=model,feature=feature,fits=len(group),
                            coefficient_mean=float(group.coefficient.mean()),coefficient_min=float(group.coefficient.min()),
                            coefficient_max=float(group.coefficient.max()),magnitude_mean=float(group.magnitude.mean()),
                            positive_fraction=float((signs>0).mean()),negative_fraction=float((signs<0).mean()),
                            sign_changes=int((np.diff(signs)!=0).sum()),raw_coefficient_mean=float(group.raw_coefficient.mean())))
    return pd.DataFrame(records)


def _paired_models(predictions,start,seed,replicates):
    gap=predictions[predictions.model=='GapLogistic'].sort_values('target_draw')
    rows=[]
    for model,group in predictions.groupby('model',sort=False):
        if model=='GapLogistic': continue
        group=group.sort_values('target_draw')
        for metric in ('hits','mean_winning_rank','recall_10','recall_15'):
            delta,low,high=paired_difference(gap[metric].to_numpy()-group[metric].to_numpy(),seed=seed,replicates=replicates)
            rows.append(dict(evaluation_start=start,model='GapLogistic',comparator=model,metric=metric,
                             difference=delta,ci_low=low,ci_high=high,targets=len(gap)))
    return rows


def _periodicity_comparison(predictions,start,seed,replicates):
    groups={name:predictions[predictions.model==name].sort_values('target_draw') for name in ('GapLogistic','GapPeriodicityLogistic')}
    base,extended=groups['GapLogistic'],groups['GapPeriodicityLogistic']
    values={}
    for name,group in groups.items():
        values[name]={metric:group[metric].to_numpy() for metric in ('hits','mean_winning_rank')}
        for k in (10,12):
            values[name][f'Top{k}_5plus']=np.array([len(set(json.loads(row.ranking)[:k])&set(json.loads(row.actual)))>=5 for row in group.itertuples()],dtype=float)
    result=[]
    for metric in values['GapLogistic']:
        delta,low,high=paired_difference(values['GapPeriodicityLogistic'][metric]-values['GapLogistic'][metric],seed=seed,replicates=replicates)
        result.append(dict(evaluation_start=start,metric=metric,difference=delta,ci_low=low,ci_high=high,targets=len(base)))
    return result


def run(args,history,guard_outputs):
    started=perf_counter()
    starts=sorted(set(args.starts))
    if (args.primary_start not in starts or min(starts)<=105 or args.end>LAST_OPEN_DRAW or
            args.end>len(history) or max(starts)>args.end or min(args.cadence,args.repeats,args.bootstraps,args.simulations)<1 or args.seed<0):
        raise ValueError('Invalid protocol or sealed end; starts must have past supervised rows and include primary start')
    root=args.reports_dir or Path(__file__).resolve().parent.parent/'reports/prize_research'
    guard_outputs(args.data,*[root/file for file in FILES])
    availability=dependencies()
    atomic_write(root/'dependency_status.json',json.dumps(availability,indent=2)+'\n')
    print(f'Dependency status: {availability}',flush=True)
    print('Exploratory only. Draw1245 remains sealed. Primary portfolio pool fixed before results.',flush=True)
    features=build_features(history,progress=lambda message:print(message,flush=True))
    atomic_write(root/'feature_sample.csv',features.head(450).to_csv(index=False))
    feature_seconds=perf_counter()-started
    comparisons,blocks,audits,contributions,paired,periodicity=[],[],[],[],[],[]
    configurations={}
    primary=None
    for start in starts:
        def on_fit(name,model,training):
            if name in ('GapLogistic','GapPeriodicityLogistic'):
                audits.extend(dict(evaluation_start=start,model=name,**item) for item in coefficient_audit(model))
        def on_score(name,model,current,scores):
            if name in ('GapLogistic','GapPeriodicityLogistic'):
                contributions.extend(dict(evaluation_start=start,model=name,**item) for item in ranking_contributions(model,current))
        factories=_factories(args.seed,extra=start==args.primary_start and not args.core_only)
        predictions,_=evaluate(history,features,factories,start=start,end=args.end,cadence=args.cadence,seed=args.seed,
                               reserve_latest=False,fit_callback=on_fit,score_callback=on_score,
                               progress=lambda message:print(f'Start{start}: {message}',flush=True))
        configurations[str(start)]=predictions.attrs['model_configurations']
        summary=summarize_rankings(predictions,simulations=args.simulations,bootstraps=args.bootstraps,seed=args.seed)
        pair_rows=_paired_models(predictions,start,args.seed,args.bootstraps)
        # Reuse exactly the same bootstrap stream for the repeated gap-vs-random
        # and gap-vs-heuristic tables, avoiding Monte Carlo discrepancies.
        gap_random=next(row for row in pair_rows if row['comparator']=='RandomModel' and row['metric']=='hits')
        summary['comparison'].loc[summary['comparison'].model=='GapLogistic',['paired_ci_low','paired_ci_high']]=[gap_random['ci_low'],gap_random['ci_high']]
        comparisons.append(summary['comparison'].assign(evaluation_start=start))
        blocks.append(summary['time_blocks'].assign(evaluation_start=start))
        paired.extend(pair_rows)
        periodicity.extend(_periodicity_comparison(predictions,start,args.seed,args.bootstraps))
        if start==args.primary_start: primary=predictions
    ranking_seconds=perf_counter()-started-feature_seconds
    audit_table=pd.DataFrame(audits)
    contribution_table=pd.DataFrame(contributions).groupby(['evaluation_start','model','training_cutoff','feature'],sort=False).agg(
        targets=('target_draw','count'),cross_number_std=('cross_number_std','mean'),
        mean_abs_rank_shift_without_term=('mean_abs_rank_shift_without_term','mean'),
        contribution_min=('contribution_min','min'),contribution_max=('contribution_max','max')).reset_index()
    rank_summary=pd.concat(comparisons,ignore_index=True)
    tables=dict(coefficient_audit=audit_table,coefficient_stability=_stability(audit_table),ranking_contributions=contribution_table,
                ranking_comparisons=rank_summary,ranking_time_blocks=pd.concat(blocks,ignore_index=True),ranking_audit=primary,
                gap_vs_heuristics=pd.DataFrame(paired),gap_periodicity_comparison=pd.DataFrame(periodicity))
    # Persist ranking work before the longer portfolio experiment.
    for name,table in tables.items(): atomic_write(root/f'{name}.csv',table.to_csv(index=False))
    pool_rows,pool_summary=candidate_reports(primary,simulations=args.simulations,bootstraps=args.bootstraps,seed=args.seed)
    pool_blocks=[]
    for label,targets in zip(('early','middle','recent'),np.array_split(np.sort(primary.target_draw.unique()),3)):
        for (model,k),group in pool_rows[pool_rows.target_draw.isin(targets)].groupby(['model','pool_size']):
            pool_blocks.append(dict(block=label,model=model,pool_size=k,targets=len(group),
                                    ge5_events=int((group.winners>=5).sum()),ge6_events=int((group.winners==6).sum())))
    tables.update(candidate_pools=pool_rows,candidate_summary=pool_summary,candidate_time_blocks=pd.DataFrame(pool_blocks),
                  pool_5plus_events=pool_rows[pool_rows.winners>=5])
    for name in ('candidate_pools','candidate_summary','candidate_time_blocks','pool_5plus_events'):
        atomic_write(root/f'{name}.csv',tables[name].to_csv(index=False))
    portfolio_started=perf_counter()
    portfolio_rows,events=evaluate_portfolios(history,primary,pool_size=args.pool_size,repeats=args.repeats,
                                             seed=args.seed,progress=lambda message:print(message,flush=True))
    portfolio_summary,portfolio_replicates=portfolio_reports(portfolio_rows,bootstraps=args.bootstraps,seed=args.seed)
    portfolio_blocks=[]
    for label,targets in zip(('early','middle','recent'),np.array_split(np.sort(primary.target_draw.unique()),3)):
        part=portfolio_rows[portfolio_rows.target_draw.isin(targets)]
        for keys,group in part.groupby(['model','method','budget','repeat']):
            model,method,budget,repeat=keys
            portfolio_blocks.append(dict(block=label,model=model,method=method,budget=budget,repeat=repeat,targets=len(group),
                                         mean_best_match=float(group.best_match.mean()),draws_ge5=int(group.has5.sum()),
                                         prize2=int(group.prize2.sum()),prize3=int(group.prize3.sum())))
    comparison=rank_summary[rank_summary.evaluation_start==args.primary_start].copy()
    for k in (6,8,10,12,15):
        selected=pool_summary[pool_summary.pool_size==k].set_index('model')
        comparison[f'Top{k}_5plus']=comparison.model.map(selected.ge5_rate)
        comparison[f'Top{k}_6of6']=comparison.model.map(selected.ge6_rate)
    tables.update(portfolio_draws=portfolio_rows,portfolio_summary=portfolio_summary,portfolio_replicates=portfolio_replicates,
                  portfolio_time_blocks=pd.DataFrame(portfolio_blocks),prize_events=events,comparison=comparison,
                  uniform_portfolio_reference=random_portfolio_reference(primary.target_draw.nunique(),simulations=args.simulations,seed=args.seed))
    for name in ('portfolio_draws','portfolio_summary','portfolio_replicates','portfolio_time_blocks','prize_events','comparison','uniform_portfolio_reference'):
        atomic_write(root/f'{name}.csv',tables[name].to_csv(index=False))
    versions={package:importlib.metadata.version(package) for package in ('numpy','pandas','scipy')}
    metadata=dict(sealed_from=1245,source_last_draw=int(history.draw_no.max()),source_prefix_sha256=prefix_hash(args.data),
                  hash_scope='Open CSV prefix only, normalized newlines; sealed suffix not read',feature_rows=len(features),
                  configuration=dict(starts=starts,primary_start=args.primary_start,end=args.end,cadence=args.cadence,seed=args.seed,
                                     portfolio_pool=args.pool_size,budgets=[1,5,10,20],repeats=args.repeats,
                                     bootstraps=args.bootstraps,block_length=26,simulations=args.simulations,tuning='none'),
                  model_configurations=configurations,versions=versions,dependencies=availability,
                  runtime_seconds=round(perf_counter()-started,3),feature_seconds=round(feature_seconds,3),
                  ranking_seconds=round(ranking_seconds,3),portfolio_seconds=round(perf_counter()-portfolio_started,3),
                  rows={name:len(table) for name,table in tables.items()},exact_uniform_ticket_prizes=exact_ticket_prizes(),
                  warnings=['Exploratory reuse of historical evaluation data after gap-model selection; not independent confirmation.',
                            'Start windows overlap and refit phases differ; they are not independent replications.',
                            'Rare-event Clopper-Pearson intervals assume independent Bernoulli draws; paired block intervals are descriptive.',
                            'Zero-event bootstrap intervals may degenerate; consult positive exact upper bounds.',
                            'Replicate portfolios share actual draws; comparisons bootstrap draws after averaging seeds.',
                            'Multiple models, pool sizes, budgets and strategies; isolated prize events are not evidence of skill.',
                            'No profitability calculation or claim of predictability.'])
    atomic_write(root/'experiment.json',json.dumps(metadata,indent=2,allow_nan=False)+'\n')
    print(rank_summary[rank_summary.model=='GapLogistic'][['evaluation_start','targets','avg_hits','delta_vs_random','paired_ci_low','paired_ci_high']].to_string(index=False))
    print(comparison[['model','avg_hits','Top8_5plus','Top10_5plus','Top12_5plus','Top15_5plus','Top12_6of6']].to_string(index=False))
    print(f'Runtime {metadata["runtime_seconds"]}s. Reports: {root}. Exploratory only; draw1245 remains sealed.')
