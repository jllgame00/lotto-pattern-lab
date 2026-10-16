"""Phase7-only immutable publication; never fetches or evaluates a result."""
import csv
import json
from pathlib import Path
import re
from hashlib import sha256
from src.freeze_artifacts import digest,REGISTRY_FIELDS,registry_rows,registry_lock
from src.models.predictive import rank_numbers
from src.models.base import validate_ticket

MODEL_NAMES={'GapConditionedTranslationModel','GapConditionedChainModel'}


def frozen_configuration(name):
    """Version-specific contract: later model default changes cannot invalidate old evidence."""
    chain=name=='GapConditionedChainModel'
    return dict(model=name,version='phase7-gap3d-v1',min_dt=1,max_dt=52,max_dn=15,direction='both',
        top_rules=20,prior_opportunities=100.,min_history=104,minimum_predecessors=2 if chain else 1,
        score_definition='p+(1-p)*weighted fraction of eligible rules with observed source support; not probability',
        representation='quantile',min_support=20 if chain else 100,destination_state_used=False,
        condition='most recent observed source pre-draw gap; never-seen excluded',
        state_version='pre-draw-gap-v1',bin_fit='training pre-states only; frozen between refits')


def verify_prior(root,protected):
    root=Path(root).resolve()
    for relative,expected in protected.items():
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or path.is_relative_to(root/'phase7'):
            raise ValueError('Invalid protected artifact path')
        if digest(path)!=expected: raise ValueError(f'Prior prospective artifact changed: {relative}')


def validate(payload):
    if (payload.get('schema_version')!='phase7-gap3d-v1' or payload.get('phase')!=7 or
        type(payload.get('training_cutoff')) is not int or not 104<=payload['training_cutoff']<=1245 or
        type(payload.get('target_draw')) is not int or payload.get('target_draw')!=payload['training_cutoff']+1 or payload.get('status')!='FROZEN_UNEVALUATED' or
        payload.get('future_result_accessed') is not False or payload.get('seed')!=42 or
        not re.fullmatch(r'draw\d+_phase7_gap3d_[A-Za-z0-9_]+',payload.get('experiment_id',''))):
        raise ValueError('Invalid Phase7 frozen scope/identity/status')
    if not payload['experiment_id'].startswith(f"draw{payload['target_draw']}_phase7_gap3d_"):
        raise ValueError('Experiment identity and target mismatch')
    for field in ('created_at','latest_training_date','git_sha','dataset_hash','feature_version'):
        if not isinstance(payload.get(field),str) or not payload[field]: raise ValueError('Missing provenance: '+field)
    if (not re.fullmatch('[0-9a-f]{64}',payload['dataset_hash']) or
        type(payload.get('git_dirty')) is not bool or not isinstance(payload.get('environment'),dict)):
        raise ValueError('Invalid provenance metadata')
    if 'sources' in payload or 'source_hashes' in payload:
        if set(payload.get('sources',{}))!=set(payload.get('source_hashes',{})): raise ValueError('Source archive mismatch')
        for name,source in payload['sources'].items():
            if sha256(source.encode()).hexdigest()!=payload['source_hashes'][name]: raise ValueError('Embedded source integrity mismatch')
    if set(payload.get('models',{}))!=MODEL_NAMES or set(payload.get('fitted_models',{}))!=MODEL_NAMES:
        raise ValueError('Exactly the two predeclared primary tracks required')
    for name,track in payload['models'].items():
        expected=frozen_configuration(name)
        fitted=payload['fitted_models'][name]
        if (track['configuration']!=expected or fitted.get('configuration')!=expected or
            not isinstance(fitted.get('rules'),list) or not isinstance(fitted.get('encoder'),dict) or
            fitted['encoder'].get('training_cutoff')!=payload['training_cutoff'] or
            fitted['encoder'].get('version')!='pre-draw-gap-v1'):
            raise ValueError('Complete predeclared fitted configuration/rule/encoder audit required')
        encoder=fitted['encoder']
        if (not {'clip_cap','quantile_edges','relative_edges','missing_state','timing'}<=set(encoder) or
            not 0<=encoder['clip_cap']<=26 or len(encoder['quantile_edges'])!=2 or
            encoder['quantile_edges']!=sorted(encoder['quantile_edges']) or encoder['missing_state']!=-1):
            raise ValueError('Incomplete frozen encoder definitions')
        for rule in fitted['rules']:
            if (not {'delta_draw','delta_number','gap_state','opportunities','matches','weight','shrunk_rate'}<=set(rule) or
                not 1<=rule['delta_draw']<=expected['max_dt'] or not 1<=abs(rule['delta_number'])<=expected['max_dn'] or
                rule['gap_state'] not in (0,1,2) or rule['opportunities']<expected['min_support'] or
                not 0<=rule['matches']<=rule['opportunities'] or not 0<rule['weight']<1):
                raise ValueError('Invalid frozen source rule')
        scores={int(n):v for n,v in track['scores'].items()}; ranking=rank_numbers(scores)
        if track['ranking']!=ranking or track['direct_top6']!=sorted(ranking[:6]): raise ValueError('Ranking mismatch')
        if track['seed']!=42 or track['configuration'].get('representation')!='quantile' or track['configuration'].get('destination_state_used') is not False:
            raise ValueError('Predeclared causal source-gap configuration required')
        if payload['fitted_models'][name]['training_cutoff']!=payload['training_cutoff']: raise ValueError('Fitted cutoff mismatch')
        if set(track['top_k'])!=set(map(str,(6,8,10,12,15))): raise ValueError('Missing cutoffs')
        for k in (6,8,10,12,15):
            if track['top_k'][str(k)]!=ranking[:k]: raise ValueError('TopK mismatch')
        ties=[[n for n in range(1,46) if scores[n]==value] for value in sorted(set(scores.values()),reverse=True)]
        if track['tie_groups']!=[g for g in ties if len(g)>1] or track['tie_breaking']!='descending score; exact ties smaller number first':
            raise ValueError('Tie rule mismatch')
        if set(track['portfolios'])!={'weighted','coverage'} or track['candidate_pool_size']!=12: raise ValueError('Portfolio methods/pool mismatch')
        for group in track['portfolios'].values():
            if set(group)!=set(map(str,(1,5,10,20))): raise ValueError('Budget mismatch')
            for budget,tickets in group.items():
                if len(tickets)!=int(budget) or len(set(map(tuple,tickets)))!=len(tickets) or tickets!=group['20'][:int(budget)]:
                    raise ValueError('Portfolios must be unique nested prefixes')
                for ticket in tickets:
                    validate_ticket(ticket)
                    if not set(ticket)<=set(ranking[:12]): raise ValueError('Ticket outside frozen pool')


def ensure_new(directory,target):
    directory=Path(directory)
    if directory.resolve().name!='phase7': raise ValueError('Phase7 requires its own phase7 directory')
    if (directory/f'draw{target}_phase7_gap3d.reservation.json').exists() or any(int(row['target_draw'])==target for row in registry_rows(directory)):
        raise ValueError('Phase7 target already frozen or reserved; no regeneration')


def manifest(payload):
    lines=['# Phase7 gap-conditioned prospective experiment','',
        f"Experiment: {payload['experiment_id']}",f"Target: {payload['target_draw']}; cutoff: {payload['training_cutoff']}",
        f"Status: {payload['status']}",f"Created: {payload['created_at']}",f"Latest included date: {payload['latest_training_date']}",
        f"Dataset SHA-256: {payload['dataset_hash']}",f"Git SHA: {payload['git_sha']}; dirty: {payload['git_dirty']}",
        'No future result was retrieved, searched for, inspected, imported, or evaluated.',
        'Only CURRENT GAP is the third dimension. It is calculated before the target outcome.',
        'Fit on included history once; bins and cap use training pre-states only. Destination state is NOT a predictive input.',
        'No Phase7 ensemble selected. Two independent predeclared coarse-bin hypotheses; no predictive claim.',
        'Scores are support, not calibrated probabilities. Exact score ties: smaller number first.',
        'Seed42; Top12 weighted/coverage portfolios. Budgets1/5/10/20 are prefixes of one generation per method.',
        'Top8/10/12/15 hypotheses: count main winners, >=3/4/5/all6. Rare events are not proof.',
        'Environment: '+json.dumps(payload['environment'],sort_keys=True)]
    for name,track in payload['models'].items():
        lines.extend(['',f'## {name}','Configuration: '+json.dumps(track['configuration'],sort_keys=True),
            'Fitted state/rules: '+json.dumps(payload['fitted_models'][name],sort_keys=True),
            'All45 scores: '+json.dumps(track['scores'],sort_keys=True),'Complete ranking: '+str(track['ranking']),
            'Tie groups: '+str(track['tie_groups'])])
        for k in (6,8,10,12,15): lines.append(f"Top{k}: {track['top_k'][str(k)]}")
        lines.append('Direct Top6: '+str(track['direct_top6']))
        for method,group in track['portfolios'].items():
            for budget,tickets in group.items(): lines.append(f'{method}, {budget} tickets: '+json.dumps(tickets))
    lines.extend(['','## Earlier immutable artifacts',json.dumps(payload['prior_artifact_hashes'],indent=2)])
    return '\n\n'.join(lines)+'\n'


def publish_gap3d(payload,directory,*,protected):
    directory=Path(directory); validate(payload); ensure_new(directory,payload['target_draw'])
    verify_prior(directory.parent,protected)
    payload=dict(payload,prior_artifact_hashes=dict(protected))
    # Complete rendering/serialization before acquiring a permanent reservation.
    snapshot_text=json.dumps(payload,indent=2,allow_nan=False)
    manifest_text=manifest(payload)
    directory.mkdir(parents=True,exist_ok=True)
    identity=payload['experiment_id']; paths={name:directory/(identity+suffix) for name,suffix in
        [('snapshot','.json'),('manifest','_manifest.md'),('integrity','_integrity.json')]}
    with registry_lock(directory):
        ensure_new(directory,payload['target_draw'])
        with (directory/f"draw{payload['target_draw']}_phase7_gap3d.reservation.json").open('x',encoding='utf-8') as stream:
            json.dump(dict(experiment_id=identity,target_draw=payload['target_draw']),stream)
        with paths['snapshot'].open('x',encoding='utf-8') as stream: stream.write(snapshot_text)
        with paths['manifest'].open('x',encoding='utf-8') as stream: stream.write(manifest_text)
        hashes={p.name:digest(p) for name,p in paths.items() if name!='integrity'}
        with paths['integrity'].open('x',encoding='utf-8') as stream: json.dump(hashes,stream,indent=2)
        row={key:payload[key] for key in REGISTRY_FIELDS if key in payload}
        row.update(snapshot_path=paths['snapshot'].name,snapshot_hash=digest(paths['snapshot']),
            manifest_path=paths['manifest'].name,manifest_hash=digest(paths['manifest']),integrity_path=paths['integrity'].name)
        registry=directory/'registry.csv'; exists=registry.exists()
        with registry.open('a',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=REGISTRY_FIELDS)
            if not exists: writer.writeheader()
            writer.writerow(row)
    verify_gap3d(paths['snapshot']); verify_prior(directory.parent,protected)
    return paths


def verify_gap3d(path):
    path=Path(path); payload=json.loads(path.read_text(encoding='utf-8')); validate(payload)
    identity=payload['experiment_id']
    if path.name!=identity+'.json': raise ValueError('Snapshot identity mismatch')
    integrity=json.loads(path.with_name(identity+'_integrity.json').read_text(encoding='utf-8'))
    expected_names={path.name,identity+'_manifest.md'}
    if set(integrity)!=expected_names: raise ValueError('Integrity record members mismatch')
    for name,value in integrity.items():
        if digest(path.with_name(name))!=value: raise ValueError('Artifact integrity mismatch')
    matches=[r for r in registry_rows(path.parent) if r['experiment_id']==identity]
    if len(matches)!=1: raise ValueError('Registry entry missing or duplicated')
    row=matches[0]
    for key in ('target_draw','training_cutoff','created_at','git_sha','dataset_hash','status'):
        if row[key]!=str(payload[key]): raise ValueError('Registry metadata mismatch')
    for key,name in [('snapshot_path',path.name),('manifest_path',identity+'_manifest.md'),('integrity_path',identity+'_integrity.json')]:
        if row[key]!=name: raise ValueError('Registry path mismatch')
    if row['snapshot_hash']!=digest(path) or row['manifest_hash']!=integrity[identity+'_manifest.md']: raise ValueError('Registry integrity mismatch')
    verify_prior(path.parent.parent,payload['prior_artifact_hashes'])
    return payload
