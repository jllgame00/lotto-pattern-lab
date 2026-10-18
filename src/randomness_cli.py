"""H25 offline randomness audit. No predictor, ensemble, or publication action."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from time import perf_counter
import numpy as np
import pandas as pd
from .optimal_transport_cli import archive_inventory,load_source
from .random_matrix_cli import dump
from .analysis.randomness_battery import TRACKS,SCOPES,metric_vector,scope_histories,track_view
from .analysis.randomness_null import null_search,inventory_hash
from .analysis.randomness_omnibus import leave_self_out,meta_scores,compare_scores,leave_one_family_out,scientific_status,SCORES

ROOT=Path(__file__).resolve().parents[1]


def guard(directory):
    directory=Path(directory).resolve()
    if not directory.is_relative_to((ROOT/'reports/randomness_battery').resolve()):raise ValueError('H25 outputs must stay under reports/randomness_battery')
    directory.mkdir(parents=True,exist_ok=True);return directory


def verified_archive(archive):
    record=archive_inventory(archive)
    if record['status']!='VERIFIED':
        failed=[c for c in record['checks'] if not c['verified']]
        detail=failed if failed else [dict(reason=record['status'],files=len(record['files']))]
        raise ValueError('PROSPECTIVE_ARCHIVE_STATUS=FAILURE '+json.dumps(detail,ensure_ascii=False))
    return record


def prepare(directory):
    if (directory/'starting_state.json').exists():raise FileExistsError('Starting record exists')
    root=subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=ROOT,text=True).strip()
    if root!='D:/univ/personal/lotto-pattern-lab':raise ValueError('Unexpected Git root; STOP')
    allowed={'.gitignore','README.md','docs/README.md','docs/research-ideas.md','src/cli.py'}
    tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    artifacts={name:sha256((ROOT/name).read_bytes()).hexdigest() for name in tracked if name not in allowed and (ROOT/name).is_file()}
    archive=verified_archive(ROOT/'reports/prospective')
    dump(directory/'starting_state.json',dict(root=root,branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),artifacts=artifacts,archive=archive,
        initial_worktree='clean (verified before Phase26 implementation)',research_cutoff=1245,draw1246_used=False))
    print(f"Archive {archive['status']}: {len(archive['files'])}files/{len(archive['checks'])}recorded hashes",flush=True)


def score_pool(directory,track,scope,raw,null_values):
    a=np.vstack((raw['values'],null_values));normal=leave_self_out(a,raw['orientations'])
    meta=meta_scores(normal['z'],normal['p'],raw['families'])
    path=directory/f'battery_{track}_{scope}.npz'
    np.savez_compressed(path,raw=a,z=normal['z'],p=normal['p'],center=normal['center'],scale=normal['scale'],
        scores=meta['scores'],family_max=meta['family_max'],weights=meta['weights'])
    units=[dict(key=key,value=a[0,j],z=normal['z'][0,j],p=normal['p'][0,j],
        peer_center=normal['center'][0,j],peer_scale=normal['scale'][0,j],**raw['metadata'][j]) for j,key in enumerate(raw['keys'])]
    pd.DataFrame(units).to_csv(directory/f'units_{track}_{scope}.csv',index=False)
    comparison=[dict(track=track,scope=scope,era_scan_adjusted_p=min(1.,18*r['global_p']) if scope!='full' else None,**r)
                for r in compare_scores(meta['scores'])]
    families=[]
    for j,name in enumerate(meta['family_names']):
        observed=meta['family_max'][0,j];null=meta['family_max'][1:,j]
        p=(1+int(np.sum(null>=observed)))/len(a)
        indices=np.flatnonzero(np.array(raw['families'])==name);best=int(indices[np.argmax(normal['z'][0,indices])])
        contribution=float(np.mean(np.clip(normal['z'][0,indices]-1,0,4)))
        families.append(dict(track=track,scope=scope,family=name,real_max=observed,global_p=p,
            family_adjusted_p=min(1.,len(meta['family_names'])*p),units=len(indices),strongest_key=raw['keys'][best],
            strongest_raw=a[0,best],strongest_unit_p=normal['p'][0,best],mean_bounded_anomaly=contribution))
    summary=dict(track=track,scope=scope,units=len(raw['keys']),family_names=meta['family_names'],
        inventory_hash=inventory_hash(raw),representation_hash=raw['representation_hash'],
        strongest_unit=raw['keys'][int(np.argmax(normal['z'][0]))],strongest_z=float(normal['z'][0].max()),
        hc_threshold=meta['hc'][0]['threshold'],hc_effective_units=meta['hc'][0]['effective_units'],
        triple_support=raw['details']['triple_support'],score_names=list(SCORES),comparison=comparison)
    if scope=='full':
        leave=leave_one_family_out(normal['z'],normal['p'],raw['families']);rows=[];arrays={}
        for removed,entry in leave.items():
            arrays[removed]=entry['scores']
            rows.extend(dict(track=track,removed_family=removed,**r) for r in entry['comparison'])
        pd.DataFrame(rows).to_csv(directory/f'leave_family_out_{track}.csv',index=False)
        np.savez_compressed(directory/f'leave_family_out_{track}.npz',**arrays)
    return summary,comparison,families


def analyze(x,directory):
    scopes=scope_histories(x)
    if any((directory/name).exists() for name in ('real_inventory.json','null_progress.jsonl','analysis_metadata.json')):
        raise FileExistsError('Complete/partial battery evidence exists')
    began=perf_counter();actual={};inventory={}
    for scope,source in scopes.items():
        raw=metric_vector(source);actual[scope]=raw
        inventory[scope]={k:raw[k] for k in ('draws','keys','families','orientations','metadata','space','representation_hash','details')}
    dump(directory/'real_inventory.json',inventory);np.save(directory/'binary_series.npy',x)
    with (directory/'null_progress.jsonl').open('x',encoding='utf-8') as stream:
        def progress(row):
            for scope,entry in row['scopes'].items():
                expected=track_view(actual[scope],row['track'])
                if entry['inventory_hash']!=inventory_hash(expected):raise ValueError('Complete battery search mismatch')
            record=dict(track=row['track'],replicate=row['replicate'],scopes={scope:{k:v for k,v in entry.items() if k!='raw_values'} for scope,entry in row['scopes'].items()})
            stream.write(json.dumps(record,allow_nan=False)+'\n');stream.flush()
            if (row['replicate']+1)%10==0:print(f"{row['track']} {row['replicate']+1}/199, {perf_counter()-began:.1f}s",flush=True)
        rows=null_search(x,progress=progress)
    comparisons=[];family_rows=[];summaries={}
    for track in TRACKS:
        selected=[row for row in rows if row['track']==track]
        arrays={scope:np.array([row['scopes'][scope]['raw_values'] for row in selected]) for scope in SCOPES}
        np.savez_compressed(directory/f'raw_null_{track}.npz',**arrays)
        for scope in SCOPES:
            raw=track_view(actual[scope],track)
            summary,comparison,families=score_pool(directory,track,scope,raw,arrays[scope])
            summaries[f'{track}_{scope}']=summary;comparisons.extend(comparison);family_rows.extend(families)
            print(f'Omnibus {track}/{scope} complete',flush=True)
    pd.DataFrame(comparisons).to_csv(directory/'omnibus_comparison.csv',index=False)
    pd.DataFrame(family_rows).to_csv(directory/'family_comparison.csv',index=False)
    dump(directory/'real_summary.json',summaries)
    status=scientific_status(comparisons)
    dump(directory/'analysis_metadata.json',dict(research_cutoff=1245,seed=260042,replicates_per_track=199,
        scopes={'full':[1,1245],'early':[1,415],'middle':[416,830],'recent':[831,1245]},
        iid_units=2200,fixed_margin_units=2147,main_full_histories=398,main_era_histories=1194,
        normalization='200-row augmented exchangeable pool; every row uses OTHER199, conservative ranks',
        shape_reference=dict(seed=260001,synthetic_draws=65536),sum_threshold=1,sum_cap=4,
        weighting='Equal family weight, equal unit weight within each family',hc_p_max=.5,
        hc_effective_units='Kish weight factor only, not estimated dependent test count',
        primary_correction=6,within_track_correction=3,era_scan_correction=18,
        status=status,runtime_seconds=perf_counter()-began,workers=1,
        input_hash=sha256(x.tobytes()).hexdigest(),draw1246_used=False,predictive_model_created=False,
        ensemble_created=False,publication_executed=False))
    print(status,flush=True)


def audit(x,directory):
    from .analysis.spatiotemporal import iid_surrogate,constrained_surrogate
    scopes=scope_histories(x);baseline=json.loads((directory/'starting_state.json').read_text(encoding='utf-8'))
    inventory=json.loads((directory/'real_inventory.json').read_text(encoding='utf-8'))
    summaries=json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    metadata=json.loads((directory/'analysis_metadata.json').read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in (directory/'null_progress.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [(r['track'],r['replicate']) for r in rows]==[(t,i) for t in TRACKS for i in range(199)]
    comparison=pd.read_csv(directory/'omnibus_comparison.csv');families_table=pd.read_csv(directory/'family_comparison.csv')
    assert len(comparison)==24 and len(families_table)==68
    checks={};replayed=[]
    for ti,track in enumerate(TRACKS):
        selected=[r for r in rows if r['track']==track]
        with np.load(directory/f'raw_null_{track}.npz') as f:raw_null={k:f[k] for k in f.files}
        for scope_id,scope in enumerate(SCOPES):
            raw=track_view(metric_vector(scopes[scope]),track)
            assert raw['space']==inventory[scope]['space']
            with np.load(directory/f'battery_{track}_{scope}.npz') as f:saved={k:f[k] for k in f.files}
            a=np.vstack((raw['values'],raw_null[scope]));np.testing.assert_array_equal(saved['raw'],a)
            norm=leave_self_out(a,raw['orientations'])
            for key in ('z','p','center','scale'):np.testing.assert_array_equal(saved[key],norm[key])
            meta=meta_scores(norm['z'],norm['p'],raw['families'])
            for key in ('scores','family_max','weights'):np.testing.assert_array_equal(saved[key],meta[key])
            fresh=compare_scores(meta['scores'])
            stored=comparison[(comparison.track==track)&(comparison.scope==scope)]
            for j,row in enumerate(fresh):
                r=stored[stored.score==row['score']].iloc[0]
                np.testing.assert_allclose([r.real,r.global_p,r.track_adjusted_p,r.overall_adjusted_p],
                    [row['real'],row['global_p'],row['track_adjusted_p'],row['overall_adjusted_p']],rtol=1e-12,atol=1e-12)
            # Independently calculate representative reference sets and inclusive ranks.
            for i in (0,1,199):
                peers=a[np.arange(200)!=i];center=np.quantile(peers,.5,axis=0)
                mad=1.4826*np.quantile(abs(peers-center),.5,axis=0);std=np.std(peers,axis=0,ddof=1)
                scale=np.where(mad>1e-12,mad,np.where(std>1e-12,std,1.));signed=(a[i]-center)/scale
                orientation=np.array(raw['orientations']);z=np.where(orientation=='two_sided',abs(signed),np.where(orientation=='lower',-signed,signed))
                up=(1+np.sum(peers>=a[i],axis=0))/200;down=(1+np.sum(peers<=a[i],axis=0))/200
                p=np.where(orientation=='two_sided',np.minimum(1,2*np.minimum(up,down)),np.where(orientation=='lower',down,up))
                np.testing.assert_allclose(saved['z'][i],z,rtol=1e-12,atol=1e-12);np.testing.assert_array_equal(saved['p'][i],p)
                weights=saved['weights'];independent_sum=sum(weights[j]*min(4,max(0,z[j]-1)) for j in range(len(z)))
                thresholds=np.unique(p[p<=.5]);effective=1/sum(weights**2)
                hc=max([0.]+[np.sqrt(effective)*(sum(weights[p<=threshold])-threshold)/np.sqrt(threshold*(1-threshold)) for threshold in thresholds])
                np.testing.assert_allclose(saved['scores'][i],[max(z),independent_sum,hc],rtol=1e-11,atol=1e-11)
            # All family maxima p-values and full leave-family-out recalibration.
            for j,name in enumerate(meta['family_names']):
                p=(1+int(np.sum(meta['family_max'][1:,j]>=meta['family_max'][0,j])))/200
                r=families_table[(families_table.track==track)&(families_table.scope==scope)&(families_table.family==name)].iloc[0]
                np.testing.assert_allclose([r.real_max,r.global_p],[meta['family_max'][0,j],p],rtol=1e-12,atol=1e-12)
            if scope=='full':
                leave=leave_one_family_out(norm['z'],norm['p'],raw['families'])
                with np.load(directory/f'leave_family_out_{track}.npz') as f:
                    for removed,entry in leave.items():np.testing.assert_array_equal(f[removed],entry['scores'])
                csv=pd.read_csv(directory/f'leave_family_out_{track}.csv')
                for removed,entry in leave.items():
                    for row in entry['comparison']:
                        r=csv[(csv.removed_family==removed)&(csv.score==row['score'])].iloc[0]
                        np.testing.assert_allclose([r.global_p,r.leaveout_scan_adjusted_p],[row['global_p'],row['leaveout_scan_adjusted_p']],rtol=1e-12)
            for entry in selected:
                record=entry['scopes'][scope]
                assert record['rebuilt'] and record['row_six'] and record['inventory_hash']==inventory_hash(raw)
                if track=='fixed_margins':assert record['margins_preserved']
            for replicate in (0,198):
                child=int(np.random.SeedSequence([260042,ti,replicate,scope_id,len(scopes[scope])]).generate_state(1)[0])
                null=iid_surrogate(len(scopes[scope]),seed=child) if track=='iid' else constrained_surrogate(scopes[scope],seed=child)
                replay=track_view(metric_vector(null),track);np.testing.assert_array_equal(replay['values'],raw_null[scope][replicate])
                assert replay['representation_hash']==selected[replicate]['scopes'][scope]['representation_hash']
                replayed.append(dict(track=track,scope=scope,replicate=replicate,seed=child))
            checks[f'{track}_{scope}']=dict(units=len(raw['keys']),all_raw_to_loo_to_meta_to_p=True,
                independent_reference_rank_and_meta_checks=3,triple_support=raw['details']['triple_support'])
    assert scientific_status(comparison.to_dict('records'))==metadata['status']
    for name,digest in baseline['artifacts'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    assert baseline['archive']['status']=='VERIFIED'
    assert baseline['archive']==verified_archive(ROOT/'reports/prospective')
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==baseline['head']
    checks.update(protected_files_unchanged=len(baseline['artifacts']),archive_status=baseline['archive']['status'],
        archive_unchanged=True,head_unchanged=True,replayed_histories=replayed,draw1246_used=False,
        predictive_model_created=False,ensemble_created=False,publication_executed=False,
        limitation='All1592saved full/era raw vectors audited,16representative histories regenerated; not all1592histories replayed')
    dump(directory/'audit_result.json',checks);print('H25 audit passed',flush=True)


def add_commands(commands):
    p=commands.add_parser('randomness-battery',help='Phase26 H25 offline1..1245, audit only')
    p.add_argument('action',choices=['prepare','analyze','diagnostics','audit'])
    p.add_argument('--reports-dir',type=Path,default=ROOT/'reports/randomness_battery')


def run(args):
    directory=guard(args.reports_dir)
    if args.action=='prepare':prepare(directory);return
    if not (directory/'starting_state.json').exists():raise ValueError('Run prepare/archive verification first')
    _,x=load_source(args.data)
    if args.action=='analyze':analyze(x,directory)
    elif args.action=='audit':audit(x,directory)
    elif args.action=='diagnostics':
        from .analysis.randomness_diagnostics import diagnostics
        diagnostics(x,directory)
