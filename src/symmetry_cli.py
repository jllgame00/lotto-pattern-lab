"""Phase18 H16 offline research; no collection or prospective publication."""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.recurrence import research_matrix
from src.analysis.symmetry import (LAGS,SHIFTS,draw_metrics,exact_distribution,pooled_relation,pair_relations,
    activity_correlations,rolling_symmetry)
from src.analysis.symmetry_search import (FAMILIES,metric_vector,fit_calibration,standardize,
    complete_search,null_search,compare_maxima)
from src.analysis.spatiotemporal import lotto_matrix
from src.recurrence_cli import load_research_source,dump,summarize

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve();allowed=(ROOT/'reports/symmetry').resolve()
    if not directory.is_relative_to(allowed):raise ValueError('H16 output must stay under reports/symmetry')
    directory.mkdir(parents=True,exist_ok=True);return directory


def load_calibration(directory,n):
    path=directory/f'calibration_{n}.npz';meta=json.loads((directory/f'calibration_{n}.json').read_text())
    if sha256(path.read_bytes()).hexdigest()!=meta.pop('npz_sha256'):raise ValueError('Frozen calibration integrity mismatch')
    with np.load(path) as data:meta.update({k:data[k] for k in data.files})
    if meta['draws']!=n:raise ValueError('Calibration cutoff mismatch')
    return meta


def calibrate(directory,pilots):
    for n in (1245,900):
        if (directory/f'calibration_{n}.json').exists():load_calibration(directory,n);continue
        if (directory/f'calibration_{n}.npz').exists():raise ValueError('Calibration evidence already exists')
        began=perf_counter();c=fit_calibration(n,replicates=pilots,progress=lambda m:print(m,flush=True))
        arrays={k:c.pop(k) for k in ('mean','std','eligible','finite_count','pilot_values')}
        path=directory/f'calibration_{n}.npz';np.savez_compressed(path,**arrays)
        dump(directory/f'calibration_{n}.json',dict(c,npz_sha256=sha256(path.read_bytes()).hexdigest(),runtime_seconds=perf_counter()-began))


def benchmark(x,directory):
    c={n:load_calibration(directory,n) for n in (1245,900)};times=[]
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.3f}s",flush=True)
    progress.last=perf_counter();null_search(x,c,replicates=2,seed=180000,progress=progress)
    dump(directory/'benchmark.json',dict(seconds=times,estimated_serial_199_each_seconds=float(np.mean(times)*398),
        chosen_replicates=199,scopes=[1245,900],complete_search=True))


def analyze(x,directory,replicates,workers):
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H16 requires exact1..1245')
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    outputs=('real_summary.json','null_progress.jsonl','full_metrics.csv','development_metrics.csv','full_raw.npz',
        'development_raw.npz','binary_series.npy','null_metrics_full.npz','null_metrics_development.npz','null_maxima.csv',
        'global_null_comparison.csv','analysis_metadata.json')
    if any((directory/p).exists() for p in outputs):raise ValueError('Evidence exists; choose a new report subdirectory')
    c={n:load_calibration(directory,n) for n in (1245,900)};real={};began=perf_counter()
    for scope,n in [('full',1245),('development',900)]:
        raw=metric_vector(x[:n]);real[scope]=complete_search(raw,c[n])
        table=pd.DataFrame(raw['rows']);table['z']=standardize(raw,c[n]);table.to_csv(directory/f'{scope}_metrics.csv',index=False)
        np.savez_compressed(directory/f'{scope}_raw.npz',values=raw['values'])
    dump(directory/'real_summary.json',real);np.save(directory/'binary_series.npy',x)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            for scope in real:
                if row[scope]['space']!=real[scope]['space']:raise RuntimeError('Complete-search parity mismatch')
            record={k:({a:b for a,b in v.items() if a!='raw_values'} if k in real else v) for k,v in row.items()}
            stream.write(json.dumps(record)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,c,replicates=replicates,workers=workers,progress=progress)
    flat=[];comparison=[]
    for scope in real:
        np.savez_compressed(directory/f'null_metrics_{scope}.npz',values=np.array([r[scope]['raw_values'] for r in rows]))
        flat.extend(dict(scope=scope,null_model=r['null_model'],replicate=r['replicate'],**r[scope]['maxima']) for r in rows)
        comparison.extend(compare_maxima(real[scope],rows,scope=scope))
    pd.DataFrame(flat).to_csv(directory/'null_maxima.csv',index=False);pd.DataFrame(comparison).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,development_cutoff=900,seed=180042,
        pilots_per_scope=c[1245]['replicates'],replicates_per_null=replicates,workers=workers,
        runtime_seconds=perf_counter()-began,draw1246_used=False,publication_executed=False))


def validate_development(x,directory):
    metadata=json.loads((directory/'analysis_metadata.json').read_text())
    if metadata.get('replicates_per_null')!=199 or metadata.get('pilots_per_scope')!=32:
        raise ValueError('Canonical selection requires199 surrogates per null and32 pilots per scope')
    if metadata.get('research_cutoff')!=1245 or metadata.get('development_cutoff')!=900:raise ValueError('Canonical scope mismatch')
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H16 source requires1..1245')
    real=json.loads((directory/'real_summary.json').read_text())
    for scope,n in [('full',1245),('development',900)]:
        if real[scope]['representation_hash']!=sha256(x[:n].tobytes()).hexdigest():raise ValueError('Source integrity mismatch')
        c=load_calibration(directory,n)
        if c['replicates']!=32:raise ValueError('Canonical calibration mismatch')
    c=load_calibration(directory,900);values=np.load(directory/'development_raw.npz')['values']
    null=np.load(directory/'null_metrics_development.npz')['values'];cells=len(c['keys'])
    if values.shape!=(cells,) or null.shape!=(398,cells):raise ValueError('Incomplete development search')
    raw=dict(draws=900,keys=c['keys'],values=values);z=standardize(raw,c)
    nz=np.divide(null-c['mean'],c['std'],out=np.full_like(null,np.nan),where=np.isfinite(null)&c['eligible'][None,:])
    comparisons=pd.read_csv(directory/'global_null_comparison.csv');rows=comparisons[comparisons.scope=='development'].copy()
    maxima=pd.read_csv(directory/'null_maxima.csv');maxima=maxima[maxima.scope=='development']
    if len(rows)!=14:raise ValueError('Complete development comparisons required')
    for kind,start in [('iid',0),('fixed_margins',199)]:
        group=maxima[maxima.null_model==kind]
        if group.replicate.tolist()!=list(range(199)):raise ValueError('Null identity mismatch')
        for family in FAMILIES:
            mask=np.array(c['families'])==family;observed=float(np.nanmax(z[mask]));generated=np.nanmax(nz[start:start+199,mask],axis=1)
            if not np.allclose(generated,group[family]):raise ValueError('Null own maximum mismatch')
            match=rows[(rows.null_model==kind)&(rows.family==family)]
            if len(match)!=1:raise ValueError('Family identity mismatch')
            r=match.iloc[0];p=(1+int((generated>=observed).sum()))/200
            if r.cutoff!=900 or r.replicates!=199 or not np.isclose(r.real_max,observed) or not np.isclose(r.global_p,p) or not np.isclose(r.adjusted_p,min(1,7*p)):
                raise ValueError('Development p-value mismatch')
    return rows


def select(x,directory):
    comparisons=validate_development(x,directory)
    from src.backtest.symmetry import development_search,configuration_hash
    path=directory/'selected_configuration.json'
    if path.exists() or (directory/'development_predictions.csv').exists():raise ValueError('Development evidence exists')
    began=perf_counter();s,table=development_search(x[:900],progress=lambda m:print(m,flush=True))
    s['null_development']={f:{n:float(comparisons[(comparisons.family==f)&(comparisons.null_model==n)].adjusted_p.iloc[0])
        for n in ('iid','fixed_margins')} for f in FAMILIES}
    s['pair_model_allowed']=False
    s['pair_model_decision']='No pair predictor without corrected directional relation and temporal support; descriptive only'
    s['secondary_prediction_allowed']=False;s['mirror_transform']='46-n';s['publication_executed']=False
    with path.open('x',encoding='utf-8') as stream:json.dump(dict(selection=s,sha256=configuration_hash(s)),stream,indent=2,allow_nan=False)
    table.to_csv(directory/'development_predictions.csv',index=False)
    table.groupby(['candidate','model'],sort=False).hits.agg(['mean','count']).to_csv(directory/'development_summary.csv')
    dump(directory/'selection_runtime.json',dict(seconds=perf_counter()-began))


def compare(data,directory,cadence):
    from src.backtest.symmetry import load_selection,configuration_hash,evaluate,paired_report,correlation_report
    path=directory/'selected_configuration.json';before=path.read_bytes();s=load_selection(path)
    out=directory/f'walk_forward_{cadence}'
    if out.exists():raise ValueError('Walk-forward evidence exists')
    began=perf_counter();rows=evaluate(data,s,cadence=cadence,progress=lambda m:print(m,flush=True));out.mkdir()
    rows.to_csv(out/'predictions.csv',index=False);summarize(rows).to_csv(out/'summary.csv',index=False)
    paired_report(rows,block=cadence).to_csv(out/'paired.csv',index=False);paired_report(rows,block=52).to_csv(out/'paired_block52.csv',index=False)
    correlation_report(rows,graph_path=ROOT/f'reports/graph_hypergraph/walk_forward_{cadence}/predictions.csv',
        shape_path=ROOT/f'reports/transformed_space/walk_forward_{cadence}/predictions.csv',
        mi_path=ROOT/f'reports/information_flow/walk_forward_{cadence}/predictions.csv').to_csv(out/'rank_diversity.csv',index=False)
    if path.read_bytes()!=before:raise RuntimeError('Frozen selection changed')
    dump(out/'protocol.json',dict(start=901,end=1245,cadence=cadence,mirror_refit='everytargetprefix',
        bootstrap_replicates=2000,bootstrap_block=cadence,sensitivity_block=52,references=['RandomModel','Frequency26','GapLogistic'],
        old_models_refitted=False,selection_hash=configuration_hash(s),runtime_seconds=perf_counter()-began,draw1246_used=False))


def model_example(x,directory):
    from src.backtest.symmetry import load_selection,construct,configuration_hash
    path=directory/'historical_ranking_example.json'
    if path.exists():raise ValueError('Historical model explanation exists')
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Historical example target1245 only')
    selection=load_selection(directory/'selected_configuration.json')
    if sha256(x[:900].tobytes()).hexdigest()!=selection['development_matrix_hash']:raise ValueError('Development source mismatch')
    model=construct(selection['models']['MirrorModel']).fit(x[:1244],cutoff=1244)
    scores=model.score_matrix(x[:1244],target=1245)
    stored=pd.read_csv(directory/'walk_forward_26/predictions.csv')
    row=stored[(stored.model=='MirrorModel')&(stored.target_draw==1245)]
    if len(row)!=1:raise ValueError('Unique stored historical example required')
    old=json.loads(row.iloc[0].scores)
    if not all(np.isclose(value,old[str(number)],rtol=0,atol=1e-14) for number,value in scores.items()):raise ValueError('Stored historical score mismatch')
    dump(path,dict(target=1245,training_cutoff=1244,selection_hash=configuration_hash(selection),
        source_prefix_sha256=sha256(x[:1244].tobytes()).hexdigest(),configuration=model.configuration(),
        pooled_coefficient=model.pooled_coefficient,number_diagnostics=model.last_diagnostic,
        prospective=False,draw1246_used=False))


def pooled_uncertainty(x,*,replicates=1000,seed=180077):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<2:raise ValueError('At least2 resamples required')
    rows=[]
    for lag in LAGS:
        r=pooled_relation(x,lag);events=r.pop('event_counts');hits=r.pop('hit_counts');n=len(events);block=min(52,n)
        rng=np.random.default_rng(np.random.SeedSequence([seed,lag,n]))
        index=((rng.integers(0,n,(replicates,int(np.ceil(n/block))))[:,:,None]+np.arange(block))%n).reshape(replicates,-1)[:,:n]
        rates=hits[index].sum(1)/events[index].sum(1);lo,hi=np.quantile(rates,[.025,.975])
        rows.append(dict(lag=lag,**r,ci_low=float(lo),ci_high=float(hi),block=block,replicates=replicates,target_end=len(x)))
    return rows


def center_reference(x):
    x=research_matrix(x);rows=[]
    for lag in LAGS:
        a,b=(x,x) if lag==0 else (x[:-lag],x[lag:]);support=int(a[:,22].sum());hits=int((a[:,22]&b[:,22]).sum())
        rows.append(dict(lag=lag,source=23,target=23,support=support,hits=hits,
            rate=hits/support if support else float('nan'),expected_rate=1. if lag==0 else 6/45,primary_search=False))
    return rows


def side_balance_expectation():
    from math import comb
    rows=[]
    for center in (0,1):
        for left in range(7-center):
            right=6-center-left
            rows.append(dict(left=left,right=right,center=center,imbalance=abs(left-right),
                probability=comb(22,left)*comb(22,right)/comb(45,6)))
    expected=lambda key:float(sum(r[key]*r['probability'] for r in rows))
    return dict(distribution=rows,expected_left=expected('left'),expected_right=expected('right'),
        expected_imbalance=expected('imbalance'),center_probability=expected('center'))


def diagnostic_details(x,directory):
    outputs=('shift_relations.csv','pair_rolling.csv','side_balance_summary.json','activity_temporal_stability.csv')
    if any((directory/p).exists() for p in outputs):raise ValueError('Detailed diagnostic evidence exists')
    x=research_matrix(x);shift_rows=[]
    for shift in SHIFTS:
        labels=np.arange(1,46);mapped=46-labels+shift
        valid=(labels!=23)&(mapped>=1)&(mapped<=45)&(mapped!=labels)
        for lag in LAGS:
            r=pooled_relation(x,lag,shift=shift);r.pop('event_counts');r.pop('hit_counts')
            shift_rows.append(dict(shift=shift,lag=lag,valid_source_labels=int(valid.sum()),
                source_labels=json.dumps(labels[valid].tolist()),target_labels=json.dumps(mapped[valid].tolist()),**r))
    pd.DataFrame(shift_rows).to_csv(directory/'shift_relations.csv',index=False)
    table=pd.read_csv(directory/'full_metrics.csv');rolling=[]
    for family,kind in [('pair','pair_risk'),('anti','negative_pair_risk'),('asymmetry','directional_difference')]:
        row=table[(table.family==family)&(table.kind==kind)].sort_values('z',ascending=False,kind='stable').iloc[0]
        source=int(row.source) if np.isfinite(row.source) else int(row.pair);lag=int(row.lag)
        for W in (26,52,104):
            for end in sorted(set(range(W,len(x)+1,26))|{len(x)}):
                if W<=lag:continue
                r=pair_relations(x[end-W:end],lag,minimum_support=1);j=int(np.flatnonzero(r['source']==source)[0])
                rolling.append(dict(family=family,source=source,target=46-source,lag=lag,window=W,endpoint=end,
                    samples=W-lag,support=int(r['support'][j]),hits=int(r['hits'][j]),rate=float(r['rate'][j]),
                    baseline=float(r['baseline'][j]),risk_difference=float(r['risk_difference'][j]),
                    minimum_support=10,eligible=bool(r['support'][j]>=10),descriptive_only=True))
    pd.DataFrame(rolling).to_csv(directory/'pair_rolling.csv',index=False)
    dump(directory/'side_balance_summary.json',dict(observed_mean_imbalance=float(draw_metrics(x)['imbalance'].mean()),**side_balance_expectation()))
    leaders=json.loads((directory/'real_summary.json').read_text())['full']['leaders'];activity_rows=[]
    for family,leader in leaders.items():
        if leader['kind'] not in ('positive_activity_correlation','negative_activity_correlation'):continue
        for era,indices in [('whole',np.arange(len(x)))]+list(zip(('early','middle','recent'),np.array_split(np.arange(len(x)),3))):
            r=next(r for r in activity_correlations(x[indices]) if all(r[k]==leader[k] for k in ('pair','window','lag','direction')))
            activity_rows.append(dict(family=family,era=era,start=int(indices[0]+1),end=int(indices[-1]+1),**r))
    pd.DataFrame(activity_rows,columns=['family','era','start','end','pair','low','high','window','lag','direction','correlation','samples','eligible']).to_csv(directory/'activity_temporal_stability.csv',index=False)


def diagnostics(x,directory):
    outputs=('draw_metrics.csv','pooled_relations.csv','pair_relations.csv','activity_correlations.csv','rolling_symmetry.csv',
        'temporal_stability.csv','same_draw_summary.json','center23_reference.csv','shift_relations.csv',
        'pair_rolling.csv','side_balance_summary.json','activity_temporal_stability.csv')
    if any((directory/p).exists() for p in outputs):raise ValueError('Diagnostic evidence exists')
    draw=draw_metrics(x);pd.DataFrame(dict(draw=np.arange(1,len(x)+1),**draw)).to_csv(directory/'draw_metrics.csv',index=False)
    pd.DataFrame(pooled_uncertainty(x)).to_csv(directory/'pooled_relations.csv',index=False)
    pairs=[]
    for lag in LAGS:
        r=pair_relations(x,lag);pairs.append(pd.DataFrame(r).assign(lag=lag))
    pd.concat(pairs,ignore_index=True).to_csv(directory/'pair_relations.csv',index=False);pd.DataFrame(center_reference(x)).to_csv(directory/'center23_reference.csv',index=False)
    pd.DataFrame(activity_correlations(x)).to_csv(directory/'activity_correlations.csv',index=False)
    pd.DataFrame(rolling_symmetry(x)).to_csv(directory/'rolling_symmetry.csv',index=False)
    table=pd.read_csv(directory/'full_metrics.csv');leaders=[]
    for family,kind in [('pair','pair_risk'),('anti','negative_pair_risk'),('asymmetry','directional_difference')]:
        row=table[(table.family==family)&(table.kind==kind)].sort_values('z',ascending=False,kind='stable').iloc[0]
        lag=int(row.lag)
        source=int(row.source) if np.isfinite(row.source) else int(row.pair);target=46-source
        for era,indices in zip(('early','middle','recent'),np.array_split(np.arange(len(x)),3)):
            r=pair_relations(x[indices],lag);j=int(np.flatnonzero(r['source']==source)[0]);other=j+1 if j%2==0 else j-1
            leaders.append(dict(family=family,era=era,start=int(indices[0]+1),end=int(indices[-1]+1),source=source,target=target,lag=lag,
                support=int(r['support'][j]),hits=int(r['hits'][j]),rate=float(r['rate'][j]),baseline=float(r['baseline'][j]),
                risk_difference=float(r['risk_difference'][j]),directional_difference=float(r['rate'][j]-r['rate'][other])))
    pd.DataFrame(leaders).to_csv(directory/'temporal_stability.csv',index=False)
    dist=exact_distribution();dump(directory/'same_draw_summary.json',dict(mean_pairs=float(draw['pairs'].mean()),
        mean_symmetry=float(draw['symmetry'].mean()),mean_jaccard=float(draw['jaccard'].mean()),
        mean_imbalance=float(draw['imbalance'].mean()),center_count=int(draw['center'].sum()),max_pairs=int(draw['pairs'].max()),
        pair_count_distribution={str(k):int((draw['pairs']==k).sum()) for k in range(4)},iid_joint_distribution=dist,
        iid_expected_pairs=float(sum(r['pairs']*r['probability'] for r in dist)),
        iid_expected_symmetry=float(sum((2*r['pairs']/(6-r['center']))*r['probability'] for r in dist)),
        iid_expected_jaccard=float(sum(((2*r['pairs']+r['center'])/(12-2*r['pairs']-r['center']))*r['probability'] for r in dist))))
    diagnostic_details(x,directory)


def add_commands(commands):
    p=commands.add_parser('symmetry',help='Phase18 H16 offline research<=1245; no publication')
    p.add_argument('action',choices=['calibrate','benchmark','analyze','select','compare','sensitivity','diagnostics','details','model-example','plots'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/symmetry');p.add_argument('--pilots',type=int,default=32)
    p.add_argument('--surrogates',type=int,default=199);p.add_argument('--workers',type=int,default=4)
    p.add_argument('--cadence',type=int,choices=[13,26],default=26)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='calibrate':calibrate(directory,args.pilots);return
    data=load_research_source(args.data);x=lotto_matrix(data,cutoff=len(data))
    if len(x)!=1245:raise ValueError('Canonical H16 requires exact1..1245')
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='select':select(x,directory)
    elif args.action=='compare':compare(data,directory,args.cadence)
    elif args.action=='diagnostics':diagnostics(x,directory)
    elif args.action=='details':diagnostic_details(x,directory)
    elif args.action=='model-example':model_example(x,directory)
    elif args.action=='sensitivity':
        from src.backtest.symmetry import load_selection,sensitivity
        path=directory/'selected_configuration.json';before=path.read_bytes()
        if (directory/'later_sensitivity.csv').exists():raise ValueError('Sensitivity evidence exists')
        sensitivity(x,load_selection(path),progress=lambda m:print(m,flush=True)).to_csv(directory/'later_sensitivity.csv',index=False)
        if path.read_bytes()!=before:raise RuntimeError('Frozen selection changed')
    elif args.action=='plots':
        from src.analysis.symmetry_plots import plots
        plots(x,directory)
