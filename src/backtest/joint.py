"""Predeclared joint-state ablation and paired uncertainty on identical targets."""
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.models.translation import TranslationModel,ChainModel
from src.models.gap3d import GapConditionedTranslationModel,GapConditionedChainModel
from src.models.frequency3d import FrequencyConditionedTranslationModel,FrequencyConditionedChainModel
from src.models.joint import JointStateTranslationModel,JointStateChainModel,JointStateFrequencyBaseline

def model_factories():
    classes=(TranslationModel,ChainModel,GapConditionedTranslationModel,GapConditionedChainModel,
        FrequencyConditionedTranslationModel,FrequencyConditionedChainModel,
        JointStateFrequencyBaseline,JointStateTranslationModel,JointStateChainModel)
    return {cls.__name__:cls for cls in classes}

def frozen_protocol():
    return dict(version='phase9-evaluation-v1',start=401,end=1245,development_end=900,later_start=901,seed=42,
        selection='All settings predeclared before data inspection; no outcome-based tuning or combination',
        configurations={name:factory().configuration() for name,factory in model_factories().items()})

def validate_frozen_protocol(before,after):
    if json.dumps(before,sort_keys=True,allow_nan=False)!=json.dumps(after,sort_keys=True,allow_nan=False):
        raise ValueError('Development-frozen configuration changed during later evaluation')

def paired_comparisons(results,*,starts=(401,501,601,701,801,901),replicates=2000,seed=42):
    if results.target_draw.max()>1245 or results.duplicated(['model','target_draw']).any():raise ValueError('Unique bounded historical rows required')
    if type(replicates) is not int or replicates<1:raise ValueError('Positive replicates required')
    names=[n for n in results.model.unique() if n.startswith('JointState')];rows=[]
    for start in starts:
        subset=results[results.target_draw>=start]
        if subset.empty:continue
        for name in names:
            a=subset[subset.model==name].sort_values('target_draw');chain=name=='JointStateChainModel'
            references=['RandomModel','ChainModel' if chain else 'TranslationModel',
                'GapConditionedChainModel' if chain else 'GapConditionedTranslationModel',
                'FrequencyConditionedChainModel' if chain else 'FrequencyConditionedTranslationModel']
            if name!='JointStateFrequencyBaseline':references.append('JointStateFrequencyBaseline')
            for reference in references:
                b=subset[subset.model==reference].sort_values('target_draw')
                if a.empty or a.target_draw.tolist()!=b.target_draw.tolist():raise ValueError('Paired comparisons require identical target sets')
                n=len(a);length=min(26,n);rng=np.random.default_rng(seed)
                offsets=rng.integers(n,size=(replicates,int(np.ceil(n/length))))
                indices=((offsets[:,:,None]+np.arange(length))%n).reshape(replicates,-1)[:,:n]
                metrics={key:(a[key].to_numpy(),b[key].to_numpy()) for key in ('hits','mean_winning_rank','recall_6','recall_10','recall_15')}
                for k in (8,10,12,15):
                    x,y=a[f'pool_{k}'].to_numpy(),b[f'pool_{k}'].to_numpy();metrics[f'pool_{k}_mean']=(x,y)
                    for threshold in (5,6):metrics[f'pool_{k}_{threshold}plus']=((x>=threshold).astype(int),(y>=threshold).astype(int))
                for metric,(x,y) in metrics.items():
                    delta=x-y;low,high=np.quantile(delta[indices].mean(axis=1),[.025,.975])
                    rows.append(dict(model=name,reference=reference,evaluation_start=start,targets=n,metric=metric,
                        difference=float(delta.mean()),ci_low=float(low),ci_high=float(high),bootstrap_replicates=replicates,
                        block_length=length,degenerate=bool(low==high),direction='negative favors joint' if metric=='mean_winning_rank' else 'positive favors joint',
                        warning='Unadjusted exploratory interval; zero-event bootstrap bounds do not establish impossibility'))
    return pd.DataFrame(rows)

def comparison(data,directory,*,cadence=26,progress=print):
    from src.joint_cli import guard_reports
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.backtest.translation import walk_forward,summaries,pool_report
    from src.backtest.ranking import summarize_rankings
    began=perf_counter();directory=Path(directory);guard_reports(directory);directory.mkdir(parents=True,exist_ok=True)
    protocol=frozen_protocol()
    (directory/'frozen_development_configuration.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    features=build_prospective_features(data,scope=ProspectiveScope(len(data)),progress=progress)
    features=features[features.target_draw<=len(data)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    factories=model_factories();results=walk_forward(data,factories,start=401,cadence=cadence,gap_features=features,combined=False,progress=progress)
    validate_frozen_protocol(protocol,frozen_protocol())
    results.to_csv(directory/'prediction_audit.csv',index=False)
    tables=summaries(results);tables['paired_joint_parent']=paired_comparisons(results)
    for name,frame in tables.items():frame.to_csv(directory/f'{name}.csv',index=False)
    development=results[results.target_draw<=900]
    summarize_rankings(development)['comparison'].to_csv(directory/'development_comparison.csv',index=False)
    pool_report(development).to_csv(directory/'development_pools.csv',index=False)
    results[(results.pool_8>=5)|(results.pool_10>=5)|(results.pool_12>=5)|(results.pool_15>=5)].to_csv(directory/'five_plus_pool_events.csv',index=False)
    meta=dict(**protocol,cadence=cadence,runtime_seconds=perf_counter()-began,bootstrap_replicates=2000,bootstrap_block=26,
        configuration_unchanged_after_evaluation=True,prospective_selection='Three fixed independent joint models; no combination selected',
        window_note='Start points are nested slices of one chronological run, preserving refit schedule',
        caveat='Later historical period is later than development but not pristine after prior phases',future_result_accessed=False)
    (directory/'protocol.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    if progress:progress(tables['comparison'].query('evaluation_start==901')[['model','avg_hits','delta_vs_random','paired_ci_low','paired_ci_high']].to_string(index=False))
    return meta
