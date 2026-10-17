"""Phase10-only exclusive publisher and offline integrity validation."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import numpy as np
from scipy.special import expit
from src.freeze_artifacts import digest,prepare_track,REGISTRY_FIELDS,registry_rows,registry_lock
from src.backtest.number_space import configuration_hash
from src.models.number_space import rank_mix
from src.analysis.number_space import WINDOWS,WIDTHS,PRIMARY_KERNELS,smooth,P

NAMES={'RangeDensityModel','NeighborhoodModel','GapNeighborhoodModel'}
FLAGS=('future_result_accessed','target_result_retrieved','target_result_searched','target_result_inspected','target_result_imported','target_result_evaluated')


def configurations(s):
    if (s.get('version')!='phase10-development-v1' or s.get('gap_weight') not in (.25,.5,.75) or
        s['range']['window'] not in WINDOWS or s['range']['width'] not in WIDTHS or
        s['neighborhood']['window'] not in WINDOWS or s['neighborhood']['kernel'] not in PRIMARY_KERNELS):
        raise ValueError('Predeclared development-selected settings required')
    def base(name,w,k,width):return dict(model=name,version='phase10-number-space-v1',window=w,kernel=k,width=width,
        neighbor_only=False,prior_draws=26.,boundary='truncate and normalize remaining weights; never wrap',
        timing='target t uses completed draws<t',score='causal recent appearance rate smoothed on finite number axis')
    r=base('RangeDensityModel',s['range']['window'],'triangular1',s['range']['width']);r['score']='p+mean containing-range positive excess; prior26 draws at p'
    n=base('NeighborhoodModel',s['neighborhood']['window'],s['neighborhood']['kernel'],5)
    g=dict(n,model='GapNeighborhoodModel',gap_weight=s['gap_weight'],normalization='equal-tie percentile rank',
        score='gap_weight*gap_logistic_rank+(1-gap_weight)*neighborhood_rank')
    return dict(RangeDensityModel=r,NeighborhoodModel=n,GapNeighborhoodModel=g)


def verify_prior(root,protected):
    root=Path(root).resolve()
    for relative,h in protected.items():
        p=(root/relative).resolve()
        if not p.is_relative_to(root) or p.is_relative_to(root/'phase10'):raise ValueError('Invalid prior artifact member')
        if digest(p)!=h:raise ValueError('Prior prospective artifact changed: '+relative)


def ensure_new(directory,target):
    directory=Path(directory)
    if directory.resolve().name!='phase10':raise ValueError('Phase10 requires its own namespace')
    if (directory/f'draw{target}_phase10_numberspace.reservation.json').exists() or any(int(r['target_draw'])==target for r in registry_rows(directory)):
        raise ValueError('Phase10 target already frozen/reserved; no regeneration')


def validate(payload):
    try:_validate(payload)
    except (KeyError,TypeError,IndexError,AttributeError) as exc:raise ValueError('Malformed Phase10 prospective artifact') from exc


def _validate(p):
    cutoff=p.get('training_cutoff');target=p.get('target_draw')
    if (p.get('schema_version')!='phase10-number-space-v1' or p.get('phase')!=10 or
        type(cutoff) is not int or not 106<=cutoff<=1245 or type(target) is not int or target!=cutoff+1 or
        p.get('status')!='FROZEN_UNEVALUATED' or p.get('seed')!=42 or any(p.get(k) is not False for k in FLAGS) or
        not re.fullmatch(f'draw{target}_phase10_numberspace_[A-Za-z0-9_]+',p.get('experiment_id',''))):
        raise ValueError('Invalid Phase10 scope/status/identity')
    for key in ('created_at','latest_training_date','git_sha','dataset_hash','feature_version'):
        if not isinstance(p.get(key),str) or not p[key]:raise ValueError('Missing provenance '+key)
    if not re.fullmatch('[a-f0-9]{64}',p['dataset_hash']) or type(p.get('git_dirty')) is not bool or not isinstance(p.get('environment'),dict):
        raise ValueError('Invalid provenance')
    s=p['selection'];expected=configurations(s)
    if (type(s['development_end']) is not int or not 105<=s['development_end']<=cutoff or
        s['later_start']!=s['development_end']+1 or p['selection_hash']!=configuration_hash(s)):
        raise ValueError('Development selection must precede target and match its frozen hash')
    if not p.get('sources') or set(p['sources'])!=set(p['source_hashes']):raise ValueError('Source archive mismatch')
    for name,text in p['sources'].items():
        if sha256(text.encode()).hexdigest()!=p['source_hashes'][name]:raise ValueError('Source archive hash mismatch')
    fitted=p['fitted']
    if fitted['training_cutoff']!=cutoff or fitted['feature_cutoff']!=cutoff:raise ValueError('Fitted/feature cutoff mismatch')
    counts={}
    for w in WINDOWS:
        a=np.asarray(fitted['recent_counts'][str(w)])
        if a.shape!=(45,) or a.dtype.kind not in 'iu' or (a<0).any() or (a>w).any() or a.sum()!=6*w:
            raise ValueError('Invalid archived causal counts')
        counts[w]=a
    from src.analysis.features import GAP
    gap=fitted['gap'];scaler=gap['transformer'];coef=np.asarray(gap['coefficients_with_intercept'],float)
    current=np.asarray(fitted['current_gap_features'],float)
    if (gap['training_cutoff']!=cutoff or gap['training_rows']!=(cutoff-104)*45 or scaler['columns']!=GAP or
        coef.shape!=(len(GAP)+1,) or not np.isfinite(coef).all() or current.shape!=(45,len(GAP))):raise ValueError('Invalid gap fitting audit')
    med,means,scales=[np.asarray(scaler[key],float) for key in ('medians','means','scales')]
    if any(a.shape!=(len(GAP),) or not np.isfinite(a).all() for a in (med,means,scales)) or (scales<=0).any():raise ValueError('Invalid frozen scaler')
    current=np.where(np.isfinite(current),current,med)
    gap_values=expit(((current-means)/scales)@coef[:-1]+coef[-1])
    nr=smooth(counts[s['neighborhood']['window']]/s['neighborhood']['window'],s['neighborhood']['kernel'])
    width=s['range']['width'];w=s['range']['window'];total=np.zeros(45);denom=np.zeros(45)
    for start in range(46-width):
        excess=max(0.,(counts[w][start:start+width].sum()/width+26*P)/(w+26)-P)
        total[start:start+width]+=excess;denom[start:start+width]+=1
    computed=dict(RangeDensityModel=dict(enumerate((P+total/denom).tolist(),1)),
        NeighborhoodModel=dict(enumerate(nr.tolist(),1)),
        GapNeighborhoodModel=rank_mix(dict(enumerate(gap_values.tolist(),1)),dict(enumerate(nr.tolist(),1)),s['gap_weight']))
    if set(p['models'])!=NAMES:raise ValueError('Exactly three predeclared Phase10 tracks required')
    for name,track in p['models'].items():
        scores={int(n):v for n,v in track['scores'].items()}
        if set(scores)!=set(range(1,46)) or not np.allclose([scores[n] for n in range(1,46)],[computed[name][n] for n in range(1,46)],rtol=0,atol=1e-12):
            raise ValueError('Scores contradict archived causal inputs/fitted parameters')
        if track['configuration']!=expected[name]:raise ValueError('Selected model configuration mismatch')
        regenerated=prepare_track(scores,expected[name],seed=42,portfolios=True)
        if json.loads(json.dumps(track))!=json.loads(json.dumps(regenerated)):raise ValueError('Ranks/ties/tickets/seeds disagree with frozen scores')


def manifest(p):
    lines=['# Phase10 number-space prospective experiment','',f"Experiment: {p['experiment_id']}",
        f"Target: {p['target_draw']}; training cutoff: {p['training_cutoff']}; latest date: {p['latest_training_date']}",
        f"Status: {p['status']}; created: {p['created_at']}",f"Dataset SHA256: {p['dataset_hash']}",
        f"Git SHA: {p['git_sha']}; dirty: {p['git_dirty']}",'No future result retrieved, searched for, inspected, imported, or evaluated.',
        'Numerical adjacency is not physical machine adjacency. Experimental ranking support only; no predictive/profitability claim.',
        'Three fixed development-selected tracks; no new range-aware allocation frozen without robust historical justification.',
        'Scores descending, exact ties smaller number first. Seed42. Top12 weighted/coverage portfolios; budgets are nested prefixes.',
        'Selection: '+json.dumps(p['selection'],sort_keys=True),'Selection hash: '+p['selection_hash'],
        'Environment: '+json.dumps(p['environment'],sort_keys=True),'Fitted audit: '+json.dumps(p['fitted'],sort_keys=True)]
    for name,track in p['models'].items():
        lines.extend(['',f'## {name}','Configuration: '+json.dumps(track['configuration'],sort_keys=True),
            'All45 scores: '+json.dumps(track['scores'],sort_keys=True),'Complete ranking: '+str(track['ranking']),
            'Tie groups: '+str(track['tie_groups'])])
        for k in (6,8,10,12,15):lines.append(f"Top{k}: {track['top_k'][str(k)]}")
        lines.append('Direct Top6: '+str(track['direct_top6']))
        for method,group in track['portfolios'].items():
            for budget,tickets in group.items():lines.append(f'{method}, {budget} tickets: '+json.dumps(tickets))
    lines.extend(['','## Earlier immutable artifacts',json.dumps(p['prior_artifact_hashes'],indent=2)])
    return '\n\n'.join(lines)+'\n'


def publish(payload,directory,*,protected):
    directory=Path(directory);validate(payload);ensure_new(directory,payload['target_draw']);verify_prior(directory.parent,protected)
    p=dict(payload,prior_artifact_hashes=dict(protected));body=json.dumps(p,indent=2,allow_nan=False);human=manifest(p)
    identity=p['experiment_id'];paths={name:directory/(identity+suffix) for name,suffix in [('snapshot','.json'),('manifest','_manifest.md'),('integrity','_integrity.json')]}
    directory.mkdir(parents=True,exist_ok=True)
    with registry_lock(directory):
        ensure_new(directory,p['target_draw'])
        with (directory/f"draw{p['target_draw']}_phase10_numberspace.reservation.json").open('x',encoding='utf-8') as stream:json.dump(dict(experiment_id=identity,target_draw=p['target_draw']),stream)
        with paths['snapshot'].open('x',encoding='utf-8') as stream:stream.write(body)
        with paths['manifest'].open('x',encoding='utf-8') as stream:stream.write(human)
        hashes={q.name:digest(q) for key,q in paths.items() if key!='integrity'}
        with paths['integrity'].open('x',encoding='utf-8') as stream:json.dump(hashes,stream,indent=2)
        row={key:p[key] for key in REGISTRY_FIELDS if key in p}
        row.update(snapshot_path=paths['snapshot'].name,snapshot_hash=digest(paths['snapshot']),manifest_path=paths['manifest'].name,
            manifest_hash=digest(paths['manifest']),integrity_path=paths['integrity'].name)
        registry=directory/'registry.csv';exists=registry.exists()
        with registry.open('a',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=REGISTRY_FIELDS)
            if not exists:writer.writeheader()
            writer.writerow(row)
    verify_number_space(paths['snapshot']);return paths


def verify_number_space(path):
    path=Path(path);p=json.loads(path.read_text(encoding='utf-8'));validate(p);identity=p['experiment_id']
    if path.name!=identity+'.json':raise ValueError('Snapshot identity mismatch')
    hashes=json.loads(path.with_name(identity+'_integrity.json').read_text(encoding='utf-8'))
    if set(hashes)!={path.name,identity+'_manifest.md'}:raise ValueError('Artifact integrity member mismatch')
    for name,h in hashes.items():
        if digest(path.with_name(name))!=h:raise ValueError('Artifact integrity mismatch')
    rows=[r for r in registry_rows(path.parent) if r['experiment_id']==identity]
    if len(rows)!=1:raise ValueError('Registry entry missing/duplicated')
    row=rows[0]
    for key in ('target_draw','training_cutoff','created_at','git_sha','dataset_hash','status'):
        if row[key]!=str(p[key]):raise ValueError('Registry metadata mismatch')
    for key,name in [('snapshot_path',path.name),('manifest_path',identity+'_manifest.md'),('integrity_path',identity+'_integrity.json')]:
        if row[key]!=name:raise ValueError('Registry path mismatch')
    if row['snapshot_hash']!=digest(path) or row['manifest_hash']!=hashes[identity+'_manifest.md']:raise ValueError('Registry integrity mismatch')
    verify_prior(path.parent.parent,p['prior_artifact_hashes']);return p
