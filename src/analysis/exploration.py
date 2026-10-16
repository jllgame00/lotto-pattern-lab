"""Reproducible exploratory report orchestration; never used by predictors."""
from dataclasses import asdict
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
import scipy

from src.collect.collector import atomic_write
from src.collect.dataset import RAW_COLUMNS, validate_history
from .series import binary_series
from .statistics import inspect_number
from .periodicity import PeriodicityConfig, autocorrelation_analysis, spectral_analysis, permutation_comparison
from .temporal import calendar_stats, rolling_stats, selected_numbers, selected_windows
from .regimes import detect_regimes, recurrence_stats

TABLE_NAMES=['number_history_stats','appearance_history','yearly_number_stats','monthly_number_stats',
             'year_month_number_stats','rolling_number_stats','periodicity_regimes','regime_recurrence',
             'periodicity_null']
WARNINGS=[
    'Exploratory descriptions, not predictions or statistically established cycles.',
    '45 numbers, many lags, frequencies and overlapping windows create multiple-testing and selection risk.',
    'Rolling windows are highly dependent; regime boundaries refer to endpoints, not exact change points.',
    'Completed gaps omit censored boundaries; few gaps give unstable estimates. Missing scores are not zero.',
    'Spectral periods require minimum cycles; adjacent bins and harmonics can describe the same pattern.',
    'Null shuffles preserve count and test temporal ordering only, conditional on each fixed scope.',
    'Bonferroni applies only to 45 numbers times fixed full/latest-window scopes. It does not validate selected rolling peaks, regimes, recurrence or repeated parameter searches.',
    'Recurrence candidates are heuristics after combining overlapping support windows; no recurrence significance test has been performed.',
    'Calendar tables, recurrence summaries and full-history plots are retrospective; do not feed these exports into historical predictions.',
]


def _jsonable(value):
    if isinstance(value,dict): return {str(k):_jsonable(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)): return [_jsonable(v) for v in value]
    if isinstance(value,pd.Timestamp): return value.isoformat()
    if isinstance(value,np.generic): value=value.item()
    if isinstance(value,float) and not np.isfinite(value): return None
    return value


def analyze_history(history,numbers=None,windows=(26,52,104),config=None,permutations=199,seed=42,
                    percentile=90,min_history=52,min_length=3,progress=None):
    start=perf_counter()
    config=config or PeriodicityConfig()
    numbers,windows=selected_numbers(numbers),selected_windows(windows)
    # Validate simulation options even if every requested scope is unavailable.
    permutation_comparison([],config,permutations=permutations,seed=seed)
    data=validate_history(history)
    if progress: progress(f'Analyzing {len(numbers)} numbers through draw {len(data)}; {permutations} shuffles per eligible fixed scope.')
    binary=binary_series(data)
    tables={}
    summaries={number:inspect_number(data,number) for number in numbers}
    overall=[]
    events=[]
    for number,summary in summaries.items():
        row={k:v for k,v in summary.items() if k not in ('recent','warnings')}
        for name in ('appearance_draws','appearance_intervals'):
            row[name]=json.dumps(row[name])
        overall.append(row)
        previous=None
        for draw in summary['appearance_draws']:
            events.append(dict(number=number,draw_no=draw,draw_date=data.iloc[draw-1].draw_date,
                               gap_since_previous=draw-previous if previous is not None else None))
            previous=draw
    tables['number_history_stats']=pd.DataFrame(overall)
    tables['appearance_history']=pd.DataFrame(events,columns=['number','draw_no','draw_date','gap_since_previous'])
    for grouping,name in [('year','yearly_number_stats'),('month','monthly_number_stats'),('year_month','year_month_number_stats')]:
        tables[name]=calendar_stats(data,grouping,numbers)
    rolling_start=perf_counter()
    if progress: progress('Calendar tables ready; calculating trailing windows and prior-history regimes...')
    rolling=rolling_stats(data,numbers,windows,config)
    labeled,regimes=detect_regimes(rolling,percentile,min_history,min_length)
    tables.update(rolling_number_stats=labeled,periodicity_regimes=regimes,
                  regime_recurrence=recurrence_stats(regimes,numbers,windows))
    rolling_seconds=perf_counter()-rolling_start
    if progress: progress(f'Rolling/regime analysis: {rolling_seconds:.2f}s. Running fixed-scope null comparisons...')
    null_start=perf_counter()
    null_rows=[]
    diagnostics={}
    family_size=45*(1+len(windows))
    for index,number in enumerate(numbers,1):
        x=binary[number].to_numpy()
        diagnostics[number]=dict(autocorrelation=autocorrelation_analysis(x,config),spectrum=spectral_analysis(x,config))
        for size in [0,*windows]:
            scope='full_history' if size==0 else f'latest_{size}'
            scope_seed=int(np.random.SeedSequence([seed,number,size]).generate_state(1)[0])
            if size>len(x):
                comparison=permutation_comparison([],config,permutations=permutations,seed=scope_seed)
                comparison['status']='window_unavailable'
            else:
                comparison=permutation_comparison(x if size==0 else x[-size:],config,permutations,scope_seed)
            p=comparison['p_value']
            null_rows.append(dict(number=number,scope=scope,window_size=size or len(x),end_draw=len(x),
                                  **comparison,family_size=family_size,p_bonferroni=min(1.,p*family_size) if p is not None else None))
        if progress and (index%10==0 or index==len(numbers)):
            progress(f'Null comparisons: {index}/{len(numbers)} numbers complete.')
    tables['periodicity_null']=pd.DataFrame(null_rows)
    null_seconds=perf_counter()-null_start
    fingerprint=hashlib.sha256(data[RAW_COLUMNS].to_csv(index=False,date_format='%Y-%m-%d',lineterminator='\n').encode()).hexdigest()
    warnings=list(WARNINGS)
    if 0<permutations<999:
        warnings.append(f'Only {permutations} shuffles per eligible scope: coarse p resolution 1/{permutations+1}; increase --permutations for precision. No automatic significance claim.')
    if permutations==0:
        warnings.append('Null simulations were skipped.')
    metadata=dict(cutoff_draw=int(data.draw_no.max()),cutoff_date=str(data.iloc[-1].draw_date.date()),
                  normalized_dataset_sha256=fingerprint,numbers=numbers,windows=windows,
                  configuration=dict(**asdict(config),permutations=permutations,seed=seed,percentile=percentile,
                                     min_history=min_history,min_length=min_length),
                  null_family_size=family_size,warnings=warnings,
                  versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__),
                  runtime_seconds=dict(rolling_and_regimes=rolling_seconds,null_simulations=null_seconds,total=perf_counter()-start),
                  row_counts={name:len(table) for name,table in tables.items()})
    return dict(tables=tables,metadata=metadata,summaries=summaries,diagnostics=diagnostics)


def report_paths(directory):
    directory=Path(directory)
    return [directory/f'{name}.csv' for name in TABLE_NAMES]+[directory/'temporal_analysis.json']


def write_reports(analysis,directory):
    """Write artifacts; CLI checks destinations against protected inputs first."""
    directory=Path(directory)
    for name,table in analysis['tables'].items():
        atomic_write(directory/f'{name}.csv',table.to_csv(index=False,date_format='%Y-%m-%d',lineterminator='\n'))
    payload={**analysis['metadata'],'number_summaries':analysis['summaries'],'diagnostics':analysis['diagnostics']}
    atomic_write(directory/'temporal_analysis.json',json.dumps(_jsonable(payload),indent=2,allow_nan=False)+'\n')
    return report_paths(directory)
