"""Development-only selection and matched later historical evaluation."""
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.models.number_space import NeighborhoodModel,RangeDensityModel,rank_mix
from src.analysis.number_space import WINDOWS,WIDTHS,PRIMARY_KERNELS
from hashlib import sha256
from functools import partial


def select_development(rows,names,*,end=900):
    if rows.empty or rows.target_draw.max()>end or rows.duplicated(['model','target_draw']).any():
        raise ValueError('Only unique development predictions may select settings')
    groups=[rows[rows.model==name].sort_values('target_draw') for name in names]
    if not groups or any(g.empty or g.target_draw.tolist()!=groups[0].target_draw.tolist() for g in groups):
        raise ValueError('Selection requires matching development target sets')
    return max(names,key=lambda name:float(rows[rows.model==name].hits.mean()))


def candidates():
    factories={f'Frequency{w}':partial(NeighborhoodModel,window=w,kernel='none') for w in WINDOWS}
    for w in WINDOWS:
        for width in WIDTHS:factories[f'Range_W{w}_D{width}']=partial(RangeDensityModel,window=w,width=width)
        for kernel in PRIMARY_KERNELS:
            factories[f'Neighborhood_W{w}_{kernel}']=partial(NeighborhoodModel,window=w,kernel=kernel)
            if kernel!='none':factories[f'NeighborOnly_W{w}_{kernel}']=partial(NeighborhoodModel,window=w,kernel=kernel,neighbor_only=True)
    return factories


def configuration_hash(s):return sha256(json.dumps(s,sort_keys=True,allow_nan=False).encode()).hexdigest()


def load_selection(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'));selection=payload['selection']
    if payload['sha256']!=configuration_hash(selection) or selection['later_start']!=selection['development_end']+1:
        raise ValueError('Frozen development selection integrity mismatch')
    return selection


def augment(results,selected,*,all_weights=False):
    from src.backtest.ranking import rank_metrics
    from src.models.predictive import rank_numbers
    extra=[]
    for target,group in results.groupby('target_draw',sort=False):
        by={r['model']:r for r in group.to_dict('records')}
        for alias,key in [('RangeDensityModel','range_name'),('NeighborhoodModel','neighborhood_name')]:
            extra.append(dict(by[selected[key]],model=alias))
        a=by['GapLogistic'];b=by[selected['neighborhood_name']]
        for weight in (.25,.5,.75) if all_weights else (selected['gap_weight'],):
            scores=rank_mix({int(n):v for n,v in json.loads(a['scores']).items()},
                {int(n):v for n,v in json.loads(b['scores']).items()},weight)
            ranking=rank_numbers(scores);actual=set(json.loads(a['actual']))
            row=dict(a,model=f'Combination_{weight}' if all_weights else 'GapNeighborhoodModel',
                scores=json.dumps(scores,sort_keys=True),ranking=json.dumps(ranking),**rank_metrics(ranking,actual))
            row.update({f'pool_{k}':len(set(ranking[:k])&actual) for k in (6,8,10,12,15)})
            extra.append(row)
    return pd.concat([results,pd.DataFrame(extra)],ignore_index=True)


def paired(results,starts,*,replicates=2000):
    from src.backtest.prize_reports import paired_difference
    rows=[]
    for start in starts:
        d=results[results.target_draw>=start]
        if d.empty:continue
        for name in ('RangeDensityModel','NeighborhoodModel','GapNeighborhoodModel'):
            a=d[d.model==name].sort_values('target_draw')
            for reference in ('RandomModel','Frequency26','GapLogistic'):
                b=d[d.model==reference].sort_values('target_draw')
                if a.target_draw.tolist()!=b.target_draw.tolist():raise ValueError('Paired target mismatch')
                metrics=['hits','mean_winning_rank','recall_6','recall_10','recall_15',*[f'pool_{k}' for k in (6,8,10,12,15)]]
                for metric in metrics:
                    delta,lo,hi=paired_difference(a[metric].to_numpy()-b[metric].to_numpy(),replicates=replicates)
                    rows.append(dict(model=name,reference=reference,evaluation_start=start,metric=metric,difference=delta,ci_low=lo,ci_high=hi))
                for k in (8,10,12,15):
                    for minimum in (3,4,5,6):
                        x=(a[f'pool_{k}'].to_numpy()>=minimum).astype(int);y=(b[f'pool_{k}'].to_numpy()>=minimum).astype(int)
                        delta,lo,hi=paired_difference(x-y,replicates=replicates)
                        rows.append(dict(model=name,reference=reference,evaluation_start=start,metric=f'pool_{k}_{minimum}plus',difference=delta,ci_low=lo,ci_high=hi))
    return pd.DataFrame(rows)


def comparison(data,directory,*,cadence=26,start=401,development_end=900,bootstraps=2000,progress=print,portfolios=True):
    from src.number_space_cli import guard_reports
    from src.analysis.features import build_prospective_features,GAP
    from src.prediction_scope import ProspectiveScope
    from src.backtest.translation import walk_forward,summaries
    from src.backtest.ranking import summarize_rankings
    began=perf_counter();directory=Path(directory);guard_reports(directory);directory.mkdir(parents=True,exist_ok=True)
    if cadence not in (13,26) or not 106<=start<=development_end<len(data)<=1245:raise ValueError('Invalid chronological development/later split')
    factories=candidates();selected_path=directory/'selected_configuration.json'
    def features(frame):
        f=build_prospective_features(frame,scope=ProspectiveScope(len(frame)),progress=progress)
        return f[f.target_draw<=len(frame)][['target_draw','feature_cutoff','number','appeared_next',*GAP]]
    if not selected_path.exists():
        if cadence!=26:raise ValueError('Primary cadence26 development selection must run first')
        devdata=data.iloc[:development_end].copy();f=features(devdata)
        dev=walk_forward(devdata,factories,start=start,end=development_end,cadence=26,gap_features=f,combined=False,progress=progress)
        range_name=select_development(dev,[n for n in factories if n.startswith('Range_')],end=development_end)
        neighborhood_name=select_development(dev,[n for n in factories if n.startswith('Neighborhood_')],end=development_end)
        selected=dict(version='phase10-development-v1',development_start=start,development_end=development_end,later_start=development_end+1,
            range_name=range_name,neighborhood_name=neighborhood_name,
            range={k:getattr(factories[range_name]().config,k) for k in ('window','width')},
            neighborhood={k:getattr(factories[neighborhood_name]().config,k) for k in ('window','kernel')},
            gap_weight=.5,selection_metric='highest development mean Top6 hits; ties retain declared order',
            candidate_order=list(factories),weight_order=[.25,.5,.75],ticket_allocation='predeclared coverage; not tuned',
            development_data_hash=sha256(devdata.to_csv(index=False).encode()).hexdigest())
        weight_rows=augment(dev,selected,all_weights=True)
        name=select_development(weight_rows,[f'Combination_{w}' for w in (.25,.5,.75)],end=development_end)
        selected['gap_weight']=float(name.split('_')[1])
        with selected_path.open('x',encoding='utf-8') as stream:json.dump(dict(selection=selected,sha256=configuration_hash(selected)),stream,indent=2)
        dev.to_csv(directory/'development_prediction_audit.csv',index=False)
        weight_rows.groupby('model',sort=False).agg(targets=('hits','size'),avg_hits=('hits','mean'),mean_winning_rank=('mean_winning_rank','mean')).to_csv(directory/'development_ablations.csv')
        if progress:progress('Frozen development selection: '+json.dumps(selected))
    selected=load_selection(selected_path);before=selected_path.read_bytes()
    if (selected['development_end']!=development_end or selected['development_start']!=start or
        selected['development_data_hash']!=sha256(data.iloc[:development_end].to_csv(index=False).encode()).hexdigest()):
        raise ValueError('Selection belongs to a different historical development dataset')
    f=features(data)
    audit=walk_forward(data,factories,start=start,cadence=cadence,gap_features=f,combined=False,progress=progress)
    results=augment(audit,selected)
    if before!=selected_path.read_bytes():raise RuntimeError('Frozen choices changed during later evaluation')
    out=directory/f'walk_forward_{cadence}';out.mkdir(parents=True,exist_ok=True)
    results.to_csv(out/'prediction_audit.csv',index=False)
    primary=results[results.model.isin(['RandomModel','Frequency26','GapLogistic','RangeDensityModel','NeighborhoodModel','GapNeighborhoodModel'])]
    starts=tuple(sorted({start,*[v for v in (501,601,701,801,selected['later_start']) if start<=v<=len(data)]}))
    tables=summaries(primary,starts=starts,bootstraps=bootstraps);tables['paired']=paired(primary,starts,replicates=bootstraps)
    for name,frame in tables.items():frame.to_csv(out/(name+'.csv'),index=False)
    later=primary[primary.target_draw>development_end]
    summarize_rankings(later,bootstraps=bootstraps)['comparison'].to_csv(out/'later_comparison.csv',index=False)
    results.groupby(['model',pd.cut(results.target_draw,[start-1,development_end,len(data)],labels=['development','later']).rename('period')],observed=True,sort=False).agg(
        targets=('hits','size'),avg_hits=('hits','mean'),recall_6=('recall_6','mean'),recall_10=('recall_10','mean'),recall_15=('recall_15','mean'),mean_winning_rank=('mean_winning_rank','mean')).to_csv(out/'all_ablations.csv')
    rolling=primary.sort_values('target_draw').copy()
    rolling['rolling104_hits']=rolling.groupby('model').hits.transform(lambda s:s.rolling(104,min_periods=104).mean())
    rolling[['model','target_draw','rolling104_hits']].to_csv(out/'rolling_performance.csv',index=False)
    if portfolios:
        from src.backtest.number_space_tickets import evaluate_portfolios
        evaluate_portfolios(data,primary,out,selection=selected,development_end=development_end,bootstraps=bootstraps)
    metadata=dict(version='phase10-evaluation-v1',start=start,end=len(data),development_end=development_end,later_start=development_end+1,
        selected_configuration_hash=configuration_hash(selected),selection_frozen_before_later=True,cadence=cadence,seed=42,
        input_data_hash=sha256(data.to_csv(index=False).encode()).hexdigest(),
        bootstrap_replicates=bootstraps,bootstrap_block=26,runtime_seconds=perf_counter()-began,
        historical_caveat='Later model-selection-excluded period is not a pristine holdout after prior phases',future_result_accessed=False)
    (out/'protocol.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    if progress:progress(tables['comparison'][tables['comparison'].evaluation_start==selected['later_start']].to_string(index=False));progress(f'Comparison runtime {metadata["runtime_seconds"]:.1f}s')
    return metadata
