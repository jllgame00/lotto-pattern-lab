"""Identical-target frequency/window ablations and development-only selection."""
from functools import partial
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.frequency3d import WINDOWS
from src.models.frequency3d import FrequencyConditionedTranslationModel,FrequencyConditionedChainModel
from src.models.translation import TranslationModel,ChainModel
from src.models.gap3d import GapConditionedTranslationModel,GapConditionedChainModel

def model_factories():
    factories=dict(TranslationModel=TranslationModel,ChainModel=ChainModel,
        GapConditionedTranslationModel=GapConditionedTranslationModel,GapConditionedChainModel=GapConditionedChainModel)
    for cls in (FrequencyConditionedTranslationModel,FrequencyConditionedChainModel):
        for window in WINDOWS: factories[cls.__name__+('' if window==26 else f'_W{window}')]=partial(cls,window=window)
    return factories

def select_development_windows(results,*,development_start=401,development_end=900):
    if not 105<=development_start<=development_end<1245: raise ValueError('Valid historical development interval required')
    # Filter before discovering model names, labels or objective values.
    development=results[results.target_draw.between(development_start,development_end)].copy()
    if development.duplicated(['model','target_draw']).any(): raise ValueError('Unique development rows required')
    decisions={}
    for cls in (FrequencyConditionedTranslationModel,FrequencyConditionedChainModel):
        prefix=cls.__name__;scores={};targets=None;models={}
        for window in (26,10,52):
            name=prefix+('' if window==26 else f'_W{window}')
            frame=development[development.model==name].sort_values('target_draw')
            if frame.empty or (targets is not None and frame.target_draw.tolist()!=targets): raise ValueError('Window selection requires identical nonempty development targets')
            targets=frame.target_draw.tolist();scores[window]=float(frame.hits.mean());models[window]=name
        choice=max((26,10,52),key=lambda w:scores[w])
        decisions[prefix]=dict(window=choice,selected_model=models[choice],training_selection_cutoff=development_end,
            development_start=development_start,targets=len(targets),objective='average Top6 hits',
            tie_breaking='26 then10 then52',means={str(w):v for w,v in scores.items()},
            prospective_use=False,warning='Development-selected diagnostic; primary prospective W26 remains predeclared')
    return decisions

def paired_comparisons(results,*,starts=(401,501,601,701,801,901),replicates=2000,seed=42):
    if results.target_draw.max()>1245 or results.duplicated(['model','target_draw']).any(): raise ValueError('Unique bounded historical rows required')
    if type(replicates) is not int or replicates<1: raise ValueError('Positive replicates required')
    names=[n for n in results.model.unique() if n.startswith('FrequencyConditioned')];rows=[]
    for start in starts:
        subset=results[results.target_draw>=start]
        if subset.empty: continue
        for name in names:
            a=subset[subset.model==name].sort_values('target_draw');translation='Translation' in name
            for reference in ('RandomModel','TranslationModel' if translation else 'ChainModel',
                              'GapConditionedTranslationModel' if translation else 'GapConditionedChainModel'):
                b=subset[subset.model==reference].sort_values('target_draw')
                if a.empty or a.target_draw.tolist()!=b.target_draw.tolist(): raise ValueError('Paired comparisons require identical targets')
                n=len(a);length=min(26,n);rng=np.random.default_rng(seed)
                offsets=rng.integers(n,size=(replicates,int(np.ceil(n/length))))
                indices=((offsets[:,:,None]+np.arange(length))%n).reshape(replicates,-1)[:,:n]
                metrics={key:(a[key].to_numpy(),b[key].to_numpy()) for key in ('hits','mean_winning_rank','recall_6','recall_10','recall_15')}
                for k in (8,10,12,15):
                    x,y=a[f'pool_{k}'].to_numpy(),b[f'pool_{k}'].to_numpy();metrics[f'pool_{k}_mean']=(x,y)
                    for threshold in (5,6): metrics[f'pool_{k}_{threshold}plus']=((x>=threshold).astype(int),(y>=threshold).astype(int))
                for metric,(x,y) in metrics.items():
                    delta=x-y;low,high=np.quantile(delta[indices].mean(axis=1),[.025,.975])
                    rows.append(dict(model=name,reference=reference,evaluation_start=start,targets=n,metric=metric,
                        difference=float(delta.mean()),ci_low=float(low),ci_high=float(high),
                        direction='negative favors new model' if metric=='mean_winning_rank' else 'positive favors new model',
                        bootstrap_replicates=replicates,block_length=length,degenerate=bool(low==high),
                        warning='Unadjusted exploratory paired interval; degenerate rare-event bounds do not establish absence'))
    return pd.DataFrame(rows)

def comparison(data,directory,*,cadence=26,progress=print):
    from src.frequency_cli import guard_reports
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.backtest.translation import walk_forward,summaries,pool_report
    from src.backtest.ranking import summarize_rankings
    began=perf_counter();directory=Path(directory);guard_reports(directory);directory.mkdir(parents=True,exist_ok=True)
    # Gap features are passed solely to the unchanged, separate GapLogistic baseline.
    features=build_prospective_features(data,scope=ProspectiveScope(len(data)),progress=progress)
    features=features[features.target_draw<=len(data)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    factories=model_factories()
    results=walk_forward(data,factories,start=401,cadence=cadence,gap_features=features,combined=False,progress=progress)
    results.to_csv(directory/'prediction_audit.csv',index=False)
    decisions=select_development_windows(results)
    (directory/'development_selection.json').write_text(json.dumps(decisions,indent=2),encoding='utf-8')
    tables=summaries(results);tables['paired_2d_gap_frequency']=paired_comparisons(results)
    for name,frame in tables.items(): frame.to_csv(directory/f'{name}.csv',index=False)
    development=results[results.target_draw<=900]
    summarize_rankings(development)['comparison'].to_csv(directory/'development_comparison.csv',index=False)
    pool_report(development).to_csv(directory/'development_pools.csv',index=False)
    selected=[]
    for family,decision in decisions.items():
        later=tables['comparison'][(tables['comparison'].evaluation_start==901)&(tables['comparison'].model==decision['selected_model'])].copy()
        later['selection_family']=family;later['selection_cutoff']=900;selected.append(later)
    pd.concat(selected,ignore_index=True).to_csv(directory/'development_selected_later.csv',index=False)
    results[(results.pool_8>=5)|(results.pool_10>=5)|(results.pool_12>=5)|(results.pool_15>=5)].to_csv(directory/'five_plus_pool_events.csv',index=False)
    meta=dict(start=401,end=len(data),cadence=cadence,seed=42,development_end=900,later_evaluation_start=901,
        configurations={name:factory().configuration() for name,factory in factories.items()},
        runtime_seconds=perf_counter()-began,bootstrap_replicates=2000,bootstrap_block=26,
        prospective_selection='Predeclared quantile W26 for both independent tracks; no combination selected',
        window_note='All three windows reported independently; historical start points are nested prediction slices',
        caveat='Later historical period is not pristine after prior phases. No predictive claim.',future_result_accessed=False)
    (directory/'protocol.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    if progress: progress(tables['comparison'].query('evaluation_start==901')[['model','avg_hits','delta_vs_random','paired_ci_low','paired_ci_high']].to_string(index=False))
    return meta
