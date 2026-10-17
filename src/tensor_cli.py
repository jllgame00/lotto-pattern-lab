"""Offline H15 research only; no collection, prospective or prediction action."""
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
import numpy as np
import pandas as pd
from src.analysis.tensor_search import (metric_vector,fit_calibration,complete_search,null_search,
    compare_maxima,standardize,choose_development,development_gate,temporal_correlation)
from src.analysis.tensor_representation import build_tensors
from src.analysis.tensor_decomposition import hosvd
from src.analysis.spatiotemporal import lotto_matrix
from src.recurrence_cli import load_research_source,dump

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve();allowed=(ROOT/'reports/tensor').resolve()
    if not directory.is_relative_to(allowed):raise ValueError('H15 output must stay under reports/tensor')
    directory.mkdir(parents=True,exist_ok=True);return directory


def load_calibration(directory,n):
    path=directory/f'calibration_{n}.npz';meta=json.loads((directory/f'calibration_{n}.json').read_text())
    if sha256(path.read_bytes()).hexdigest()!=meta.pop('npz_sha256'):raise ValueError('Frozen calibration integrity mismatch')
    with np.load(path) as data:meta.update({k:data[k] for k in data.files})
    return meta


def calibrate(directory,pilots):
    for n in (1245,900):
        if (directory/f'calibration_{n}.json').exists():load_calibration(directory,n);continue
        if (directory/f'calibration_{n}.npz').exists():raise ValueError('Calibration evidence already exists without metadata')
        began=perf_counter();c=fit_calibration(n,replicates=pilots,progress=lambda s:print(s,flush=True))
        arrays={k:c.pop(k) for k in ('mean','std','eligible','finite_count','pilot_values')}
        path=directory/f'calibration_{n}.npz';np.savez_compressed(path,**arrays)
        dump(directory/f'calibration_{n}.json',dict(c,npz_sha256=sha256(path.read_bytes()).hexdigest(),runtime_seconds=perf_counter()-began))


def benchmark(x,directory):
    calibrations={n:load_calibration(directory,n) for n in (1245,900)};times=[]
    def progress(row):
        now=perf_counter();times.append(now-progress.last);progress.last=now
        print(f"Benchmark {row['null_model']} {row['replicate']+1}/2: {times[-1]:.3f}s",flush=True)
    progress.last=perf_counter();null_search(x,calibrations,replicates=2,seed=170000,progress=progress)
    dump(directory/'benchmark.json',dict(seconds=times,estimated_serial_199_each_seconds=float(np.mean(times)*398),
        chosen_replicates=199,scopes=[1245,900],full_search=True))


def analyze(x,directory,replicates,workers):
    from src.analysis.recurrence import research_matrix
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H15 requires exact1..1245')
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive null counts required')
    outputs=('real_summary.json','null_progress.jsonl','full_metrics.csv','development_metrics.csv','full_raw.npz',
        'development_raw.npz','binary_series.npy','null_metrics_full.npz','null_metrics_development.npz',
        'null_maxima.csv','global_null_comparison.csv','analysis_metadata.json')
    if any((directory/p).exists() for p in outputs):raise ValueError('Evidence exists; choose a new reports subdirectory')
    calibrations={n:load_calibration(directory,n) for n in (1245,900)};real={};began=perf_counter()
    for scope,n in (('full',1245),('development',900)):
        raw=metric_vector(x[:n]);real[scope]=complete_search(raw,calibrations[n])
        table=pd.DataFrame(raw['rows']);table['z']=standardize(raw,calibrations[n]);table.to_csv(directory/f'{scope}_metrics.csv',index=False)
        np.savez_compressed(directory/f'{scope}_raw.npz',values=raw['values'])
    dump(directory/'real_summary.json',real);np.save(directory/'binary_series.npy',x)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            for scope in real:
                if row[scope]['space']!=real[scope]['space']:raise RuntimeError('Complete-search parity failure')
            record={k:({a:b for a,b in v.items() if a!='raw_values'} if k in real else v) for k,v in row.items()}
            stream.write(json.dumps(record)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['null_model']} {row['replicate']+1}/{replicates}: {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,calibrations,replicates=replicates,workers=workers,progress=progress)
    flat=[];comparisons=[]
    for scope in real:
        np.savez_compressed(directory/f'null_metrics_{scope}.npz',values=np.array([r[scope]['raw_values'] for r in rows]))
        flat.extend(dict(scope=scope,cutoff=real[scope]['draws'],null_model=r['null_model'],replicate=r['replicate'],**r[scope]['maxima']) for r in rows)
        comparisons.extend(compare_maxima(real[scope],rows,scope=scope))
    pd.DataFrame(flat).to_csv(directory/'null_maxima.csv',index=False)
    pd.DataFrame(comparisons).to_csv(directory/'global_null_comparison.csv',index=False)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,development_cutoff=900,seed=170042,
        pilots_per_scope=calibrations[1245]['replicates'],replicates_per_null=replicates,workers=workers,
        runtime_seconds=perf_counter()-began,draw1246_used=False,publication_executed=False))


def freeze_decision(raw,z,comparisons,path,*,provenance=None):
    if any(r.get('scope')!='development' or r.get('cutoff')!=900 for r in comparisons):raise ValueError('Only development comparisons permitted')
    choice=choose_development(raw,z);gate=development_gate(comparisons,cutoff=900)
    selection=dict(version='phase17-hosvd-v1',research_cutoff=1245,development_end=900,later_start=901,
        choice=choice,decision=gate,rank_candidates=dict(time=[8],number=[2,3,4,6],feature=[1,2,3]),
        normalization='fixed IID mean and std; gap clipped52; no fitted full-history scaling',
        predictive_model_created=False,prospective_capability_created=False,ensemble_candidate='NOT CURRENTLY JUSTIFIED',
        prospective_status='PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION',draw1246_used=False,publication_executed=False)
    if provenance is not None:selection['provenance']=provenance
    payload=dict(selection=selection,sha256=sha256(json.dumps(selection,sort_keys=True,allow_nan=False).encode()).hexdigest())
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(payload,stream,ensure_ascii=False,indent=2,allow_nan=False)
    return payload


def decision(x,directory):
    metadata=json.loads((directory/'analysis_metadata.json').read_text())
    if metadata.get('replicates_per_null')!=199 or metadata.get('pilots_per_scope')!=32:
        raise ValueError('Canonical decision requires199 surrogates per null and32 pilots per scope')
    if metadata.get('research_cutoff')!=1245 or metadata.get('development_cutoff')!=900:raise ValueError('Canonical scope mismatch')
    calibrations={n:load_calibration(directory,n) for n in (1245,900)}
    if any(c['draws']!=n or c['replicates']!=32 for n,c in calibrations.items()):raise ValueError('Canonical calibration scope mismatch')
    from src.analysis.recurrence import research_matrix
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical H15 source requires1..1245')
    real=json.loads((directory/'real_summary.json').read_text())
    if any(real[scope]['representation_hash']!=sha256(x[:n].tobytes()).hexdigest() for scope,n in [('full',1245),('development',900)]):
        raise ValueError('Canonical source integrity mismatch')
    c=calibrations[900]
    with np.load(directory/'development_raw.npz') as data:values=data['values']
    raw=dict(draws=900,keys=c['keys'],metadata=c['metadata'],families=c['families'],values=values)
    table=pd.read_csv(directory/'global_null_comparison.csv');rows=table[table.scope=='development'].to_dict('records')
    with np.load(directory/'null_metrics_development.npz') as data:null=data['values']
    if values.shape!=(165,) or null.shape!=(398,165):raise ValueError('Incomplete canonical development search')
    z=standardize(raw,c)
    nz=np.divide(null-c['mean'],c['std'],out=np.full_like(null,np.nan),where=np.isfinite(null)&c['eligible'][None,:])
    if len(rows)!=10:raise ValueError('Complete development comparison required')
    maxima=pd.read_csv(directory/'null_maxima.csv');maxima=maxima[maxima.scope=='development']
    for kind,start in [('iid',0),('fixed_margins',199)]:
        group=maxima[maxima.null_model==kind]
        if group.replicate.tolist()!=list(range(199)):raise ValueError('Canonical null identity mismatch')
        for family in set(c['families']):
            mask=np.array(c['families'])==family;observed=float(np.nanmax(z[mask]))
            generated=np.nanmax(nz[start:start+199,mask],axis=1)
            if not np.allclose(generated,group[family]):raise ValueError('Null global maximum mismatch')
            matches=[r for r in rows if r['null_model']==kind and r['family']==family]
            if len(matches)!=1:raise ValueError('Canonical family identity mismatch')
            row=matches[0];p=(1+int((generated>=observed).sum()))/200
            if row['replicates']!=199 or not np.isclose(row['real_max'],observed) or not np.isclose(row['global_p'],p) or not np.isclose(row['adjusted_p'],min(1,5*p)):
                raise ValueError('Canonical development comparison mismatch')
    paths=['analysis_metadata.json','development_raw.npz','null_metrics_development.npz','global_null_comparison.csv']
    paths += [f'calibration_{n}.{suffix}' for n in (900,1245) for suffix in ('json','npz')]
    provenance=dict(development_matrix_sha256=sha256(x[:900].tobytes()).hexdigest(),
        artifacts={p:sha256((directory/p).read_bytes()).hexdigest() for p in paths})
    selected=freeze_decision(raw,z,rows,directory/'selected_configuration.json',provenance=provenance)
    print(json.dumps(selected['selection']['decision']),flush=True)


def targeted_controls(x,*,seed=170777):
    output=[];rng=np.random.default_rng(seed)
    for name,rep in build_tensors(x).items():
        tensor=rep['values'];base=hosvd(tensor,(8,6,3))
        for control,changed in [('tensor_time_slice_shuffle',tensor[rng.permutation(len(tensor))]),
                ('consistent_number_label_shuffle',tensor[:,rng.permutation(45),:])]:
            fit=hosvd(changed,(8,6,3))
            output.append(dict(tensor=name,control=control,
                max_spectrum_difference=max(float(np.max(abs(a-b))) for a,b in zip(base['singular_values'],fit['singular_values'])),
                reconstruction_error_difference=float(abs(base['relative_error']-fit['relative_error'])),
                real_abs_temporal_lag1=[temporal_correlation(base['factors'][0][:,j]) for j in range(4)],
                control_abs_temporal_lag1=[temporal_correlation(fit['factors'][0][:,j]) for j in range(4)]))
    return output


def diagnostics(x,directory):
    if any((directory/p).exists() for p in ('decompositions.npz','decomposition_metadata.json','targeted_controls.json')):
        raise ValueError('Diagnostic evidence already exists')
    selection=json.loads((directory/'selected_configuration.json').read_text());s=selection['selection']
    if sha256(json.dumps(s,sort_keys=True,allow_nan=False).encode()).hexdigest()!=selection['sha256']:raise ValueError('Selection integrity mismatch')
    dump(directory/'targeted_controls.json',targeted_controls(x))
    arrays={};metadata={};frequency=x.mean(axis=0)
    for name,rep in build_tensors(x).items():
        tensor=rep['values'];fit=hosvd(tensor,(8,6,3))
        arrays[name+'_tensor']=tensor;arrays[name+'_draws']=rep['draws'];arrays[name+'_core']=fit['core'];arrays[name+'_reconstruction']=fit['reconstruction']
        for mode in range(3):
            arrays[f'{name}_factors_{mode}']=fit['factors'][mode];arrays[f'{name}_singular_{mode}']=fit['singular_values'][mode]
        metadata[name]=dict(dimensions=list(tensor.shape),features=rep['features'],metadata=rep['metadata'],
            reconstruction_error=fit['relative_error'],mode_retained_energy=list(map(float,fit['explained_energy'])),
            number_factor_frequency_correlations=[float(np.corrcoef(frequency,fit['factors'][1][:,j])[0,1]) for j in range(6)],
            core_energy_concentration=float(np.square(fit['core']).max()/np.square(fit['core']).sum()))
    np.savez_compressed(directory/'decompositions.npz',**arrays);dump(directory/'decomposition_metadata.json',metadata)


def add_commands(commands):
    p=commands.add_parser('tensor',help='Phase17 H15 offline research<=1245; no publication')
    p.add_argument('action',choices=['calibrate','benchmark','analyze','decision','diagnostics','plots'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/tensor')
    p.add_argument('--pilots',type=int,default=32);p.add_argument('--surrogates',type=int,default=199);p.add_argument('--workers',type=int,default=4)


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='calibrate':calibrate(directory,args.pilots);return
    data=load_research_source(args.data);x=lotto_matrix(data,cutoff=len(data))
    if len(x)!=1245:raise ValueError('Canonical H15 requires exact1..1245')
    if args.action=='benchmark':benchmark(x,directory)
    elif args.action=='analyze':analyze(x,directory,args.surrogates,args.workers)
    elif args.action=='decision':decision(x,directory)
    elif args.action=='diagnostics':diagnostics(x,directory)
    elif args.action=='plots':
        from src.analysis.tensor_plots import plots
        plots(x,directory)
