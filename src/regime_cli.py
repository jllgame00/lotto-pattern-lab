"""Prespecified regime/Bayesian experiments and development-frozen ensembles."""
from functools import partial
import importlib.util
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from src.analysis.features import build_features,GAP,PERIODICITY
from src.analysis.regime_research import hmm_fit_records,state_relationships,parameter_stability,null_diagnostics,plot_states
from src.backtest.ranking import evaluate,summarize_rankings,rank_metrics
from src.backtest.prize_reports import candidate_reports,portfolio_reports,random_portfolio_reference
from src.backtest.prize_experiment import evaluate_portfolios
from src.collect.collector import atomic_write
from src.models.bayesian import BayesianModel
from src.models.hazard import GapHazardModel,hazard_table
from src.models.regime import HMMModel
from src.models.ensemble import FrozenEnsemble
from src.models.predictive import FittedModel,LogisticModel,SimilarityModel,ForestModel,BoostingModel,rank_numbers
from src.models.gap_research import GapHeuristic,HEURISTICS
from src.prize_cli import dependencies
from src.research_seal import LAST_OPEN_DRAW,prefix_hash


class FrequencyModel(FittedModel):
    def __init__(self,**kwargs): super().__init__(columns=['rate_52'],**kwargs)
    def fit(self,rows,*,cutoff): self._training(rows,cutoff); return self
    def score_rows(self,rows):
        self._current(rows)
        return dict(zip(rows.number.astype(int),rows.rate_52.astype(float)))


def add_commands(commands):
    hazard=commands.add_parser('hazard-analysis',help='Empirical gap hazards, sealed retrospective prefix')
    hazard.add_argument('--reports-dir',type=Path)
    experiment=commands.add_parser('compare-regime-models',help='Causal Bayesian/HMM/hazard and frozen ensemble research')
    for name,default in [('start',601),('end',1244),('development-end',900),('cadence',26),('seed',42),
                         ('hmm-iterations',40),('null-repeats',39),('repeats',3),('bootstraps',2000),('simulations',2000)]:
        experiment.add_argument('--'+name,type=int,default=default)
    experiment.add_argument('--skip-robustness',action='store_true')
    experiment.add_argument('--reports-dir',type=Path)
    freeze=commands.add_parser('freeze-next',help='Create new offline snapshot from local canonical data, bounded at1245')
    freeze.add_argument('--reports-dir',type=Path)
    freeze.add_argument('--seed',type=int,default=42)


def factories(seed,iterations,*,extras=True):
    models={'GapLogistic':partial(LogisticModel,columns=GAP,seed=seed),
        'GapHazard':partial(GapHazardModel,seed=seed),
        'BayesianStatic':partial(BayesianModel,seed=seed),
        'BayesianRecent':partial(BayesianModel,half_life=52,seed=seed),
        'HMM2':partial(HMMModel,states=2,max_iter=iterations,seed=seed),
        'HMM3':partial(HMMModel,states=3,max_iter=iterations,seed=seed)}
    if extras:
        models.update({'Frequency52':partial(FrequencyModel,seed=seed),
            'SimilarityModel':partial(SimilarityModel,seed=seed),
            'GapPeriodicityLogistic':partial(LogisticModel,columns=GAP+PERIODICITY,seed=seed)})
        models.update({f'GapRule[{rule}]':partial(GapHeuristic,method=rule,seed=seed) for rule in HEURISTICS})
        if importlib.util.find_spec('sklearn'): models['RandomForest']=partial(ForestModel,seed=seed)
        if any(importlib.util.find_spec(n) for n in ('lightgbm','xgboost')): models['Boosting']=partial(BoostingModel,seed=seed)
    return models


def ensemble_predictions(predictions,development_end):
    dev=predictions[predictions.target_draw<=development_end]
    later=predictions[predictions.target_draw>development_end]
    groups={'GapBayes':['GapLogistic','BayesianRecent'],'GapHMM':['GapLogistic','HMM2'],
        'BayesHMM':['BayesianRecent','HMM2'],'GapBayesHMM':['GapLogistic','BayesianRecent','HMM2'],
        'All':['GapLogistic','GapHazard','BayesianStatic','BayesianRecent','HMM2','HMM3','SimilarityModel','Frequency52','GapPeriodicityLogistic']}
    groups['NoPeriodicity']=[n for n in groups['All'] if n!='GapPeriodicityLogistic']
    groups['NoSimilarity']=[n for n in groups['All'] if n!='SimilarityModel']
    records=[]; configs={}
    for group,components in groups.items():
        for method in ('rank','score'):
            name=f'Ensemble[{group},{method}]'
            ensemble=FrozenEnsemble(components,method=method,development_end=development_end)
            configs[name]=ensemble.configuration()
            for target,rows in later.groupby('target_draw'):
                scores=ensemble.score(rows.drop(columns='actual'))
                ranking=rank_numbers(scores); actual=set(json.loads(rows.iloc[0].actual))
                records.append(dict(model=name,target_draw=target,feature_cutoff=target-1,
                    training_cutoff=int(rows[rows.model.isin(components)].training_cutoff.max()),
                    weight_selection_cutoff=development_end,actual=json.dumps(sorted(actual)),
                    top6=json.dumps(ranking[:6]),ranking=json.dumps(ranking),scores=json.dumps(scores),
                    configuration=json.dumps(configs[name]),**rank_metrics(ranking,actual)))
    ensemble=FrozenEnsemble(groups['All']).select(dev,development_end=development_end)
    name='Ensemble[DevelopmentWeights]'; configs[name]=ensemble.configuration()
    for target,rows in later.groupby('target_draw'):
        scores=ensemble.score(rows.drop(columns='actual')); ranking=rank_numbers(scores)
        actual=set(json.loads(rows.iloc[0].actual))
        records.append(dict(model=name,target_draw=target,feature_cutoff=target-1,
            training_cutoff=int(rows[rows.model.isin(groups['All'])].training_cutoff.max()),weight_selection_cutoff=development_end,
            actual=json.dumps(sorted(actual)),top6=json.dumps(ranking[:6]),ranking=json.dumps(ranking),
            scores=json.dumps(scores),configuration=json.dumps(configs[name]),**rank_metrics(ranking,actual)))
    return pd.concat([later,pd.DataFrame(records)],ignore_index=True),configs


def run(args,history,guard_outputs):
    began=perf_counter(); root=args.reports_dir or Path(__file__).resolve().parent.parent/'reports/regime_research'
    def save(name,table):
        path=root/f'{name}.csv'; guard_outputs(args.data,path); atomic_write(path,table.to_csv(index=False))
    def save_json(name,value):
        path=root/f'{name}.json'; guard_outputs(args.data,path); atomic_write(path,json.dumps(value,indent=2,default=str)+'\n')
    if args.command=='compare-regime-models':
        if (not 209<=args.start<=args.development_end<args.end<=min(LAST_OPEN_DRAW,len(history)) or
            min(args.cadence,args.hmm_iterations,args.null_repeats,args.repeats,args.bootstraps,args.simulations)<1 or args.seed<0):
            raise ValueError('Invalid protocol: HMM requires104 supervised observations before start; strict dev/later split required')
        # Limit features/diagnostics to configured end even if source contains more open history.
        history=history[history.draw_no<=args.end]
    features=build_features(history,progress=lambda s:print(s,flush=True))
    save('hazard',hazard_table(features))
    if args.command=='hazard-analysis':
        save_json('hazard_metadata',dict(cutoff=int(history.draw_no.max()),source_prefix_sha256=prefix_hash(args.data),
            warning='Descriptive only; number rows are dependent. Bin intervals are marginal and not multiplicity corrected.'))
        print(f'Hazard analysis: {root}; exploratory only',flush=True); return
    fit_rows=[]; state_rows=[]; bayes_rows=[]; hazard_rows=[]
    def on_fit(name,model,training):
        if isinstance(model,HMMModel): fit_rows.extend(hmm_fit_records(name,model))
        if isinstance(model,BayesianModel):
            bayes_rows.extend(model.diagnostics().assign(model=name,training_cutoff=model.training_cutoff).to_dict('records'))
        if isinstance(model,GapHazardModel):
            hazard_rows.extend(dict(model=name,training_cutoff=model.training_cutoff,bucket=j,
                observations=int(model.counts[j]),appearances=int(model.successes[j]),probability=float(model.probabilities[j])) for j in range(8))
    def on_score(name,model,current,scores):
        if isinstance(model,HMMModel):
            for j in range(45):
                state_rows.append(dict(model=name,target_draw=int(current.target_draw.iloc[0]),number=j+1,
                    training_cutoff=model.training_cutoff,cold_probability=model.hmm.state[j,0],
                    hot_probability=model.hmm.state[j,-1],neutral_probability=model.hmm.state[j,1] if model.states==3 else np.nan,
                    score=scores[j+1]))
    print('Prespecified individual model evaluation; ensembles selected only after these predictions exist.',flush=True)
    predictions,_=evaluate(history,features,factories(args.seed,args.hmm_iterations),start=args.start,end=args.end,
        cadence=args.cadence,seed=args.seed,reserve_latest=False,fit_callback=on_fit,score_callback=on_score,
        progress=lambda s:print(s,flush=True))
    save('individual_audit',predictions)
    summary=summarize_rankings(predictions,bootstraps=args.bootstraps,simulations=args.simulations,seed=args.seed)
    save('individual_comparison',summary['comparison']); save('individual_time_blocks',summary['time_blocks'])
    fit_table=pd.DataFrame(fit_rows); state_table=pd.DataFrame(state_rows)
    save('hmm_fits',fit_table); save('hmm_states',state_table); save('hmm_parameter_stability',parameter_stability(fit_table))
    save('hmm_periodicity_relationships',state_relationships(state_table,features))
    save('bayesian_posteriors',pd.DataFrame(bayes_rows)); save('hazard_fits',pd.DataFrame(hazard_rows))
    print('Individual results exported; constructing development-frozen ensemble ablations.',flush=True)
    later,ensemble_configs=ensemble_predictions(predictions,args.development_end)
    save_json('ensemble_weights',ensemble_configs); save('later_audit',later)
    summary=summarize_rankings(later,bootstraps=args.bootstraps,simulations=args.simulations,seed=args.seed)
    save('later_comparison',summary['comparison']); save('later_time_blocks',summary['time_blocks'])
    for name,table in [('individual',predictions),('later',later)]:
        detail,concentration=candidate_reports(table,simulations=args.simulations,bootstraps=args.bootstraps,seed=args.seed)
        save(name+'_candidate_pools',detail); save(name+'_candidate_summary',concentration)
        save(name+'_pool_5plus_events',detail[detail.winners>=5])
        if name=='later':
            comparison=summary['comparison'].copy()
            for k in (6,8,10,12,15):
                selected=concentration[concentration.pool_size==k].set_index('model')
                comparison[f'Top{k}_5plus']=comparison.model.map(selected.ge5_rate)
                comparison[f'Top{k}_6of6']=comparison.model.map(selected.ge6_rate)
            save('comparison',comparison)
    print('Running equal-budget portfolios on later targets only.',flush=True)
    portfolios,events=evaluate_portfolios(history,later,pool_size=12,repeats=args.repeats,seed=args.seed,
        progress=lambda s:print(s,flush=True))
    save('portfolio_draws',portfolios); save('prize_events',events)
    portfolio_summary,replicates=portfolio_reports(portfolios,bootstraps=args.bootstraps,seed=args.seed)
    save('portfolio_summary',portfolio_summary); save('portfolio_replicates',replicates)
    save('uniform_portfolio_reference',random_portfolio_reference(later.target_draw.nunique(),simulations=args.simulations,seed=args.seed))
    print('Running count-preserving HMM null diagnostics.',flush=True)
    null,tests=null_diagnostics(features,repeats=args.null_repeats,seed=args.seed,max_iter=args.hmm_iterations)
    save('hmm_null',null); save('hmm_null_summary',tests)
    plot_states(state_table,features,root/'plots')
    robustness=[]; robust_blocks=[]
    if not args.skip_robustness:
        protocols=sorted(set([(501,26),(701,26),(601,13)])-{(args.start,args.cadence)})
        for start,cadence in protocols:
            if start>args.end: continue
            print(f'Robustness start{start} cadence{cadence}',flush=True)
            pred,_=evaluate(history,features,factories(args.seed,args.hmm_iterations,extras=False),start=start,end=args.end,
                cadence=cadence,seed=args.seed,reserve_latest=False,progress=lambda s:print(s,flush=True))
            s=summarize_rankings(pred,bootstraps=args.bootstraps,simulations=args.simulations,seed=args.seed)
            robustness.append(s['comparison'].assign(start=start,cadence=cadence))
            robust_blocks.append(s['time_blocks'].assign(start=start,cadence=cadence))
            save(f'robustness_audit_{start}_{cadence}',pred)
    if robustness:
        save('robustness',pd.concat(robustness,ignore_index=True)); save('robustness_time_blocks',pd.concat(robust_blocks,ignore_index=True))
    availability=dependencies(); availability['hmmlearn_installed']=bool(importlib.util.find_spec('hmmlearn'))
    save_json('dependency_status',availability)
    save_json('experiment',dict(research_cutoff=1244,source_last_draw=int(history.draw_no.max()),
        source_prefix_sha256=prefix_hash(args.data),configuration=vars(args),ensemble_configuration=ensemble_configs,
        model_configuration=predictions.attrs.get('model_configurations'),runtime_seconds=perf_counter()-began,
        warnings=['No pristine historical holdout: later targets were examined in prior phases.',
                  'Development-selected weights use601-900 by default; frozen evaluation901-1244.',
                  'Many exploratory models, pools, cadences, and ablations; bootstrap intervals are not familywise guarantees.',
                  'Marginal Bayesian and hazard intervals are not evidence of predictability.',
                  'HMM states can be artifacts; null comparisons are descriptive, not predictive tests.',
                  'Actual1245 and subsequent draws were not read by this experiment.']))
    print(summary['comparison'][['model','avg_hits','delta_vs_random','paired_ci_low','paired_ci_high']].to_string(index=False))
    print(f'Exploratory research complete: {root}; runtime {perf_counter()-began:.1f}s',flush=True)
