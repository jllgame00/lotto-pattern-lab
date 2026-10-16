"""Independent Phase6 publication. Never opens results or writes Phase5 files."""
import csv
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from uuid import uuid4

import numpy as np
import scipy
from src.analysis.spatiotemporal import lotto_matrix
from src.models.translation import TranslationModel,ChainModel,combine_scores
from src.prospective_experiment import strict_source,_git,ROOT
from src.freeze_artifacts import prepare_track,digest,REGISTRY_FIELDS,registry_lock,registry_rows

CANONICAL_HASH='b3de32b409c9edd3da5525ad0280d3f59cd21bf0618feda16d3947686c27a11e'


def validate_2d(payload):
    if (payload.get('schema_version')!='phase6-2d-v1' or payload.get('phase')!=6 or
        payload.get('status')!='FROZEN_UNEVALUATED' or payload.get('target_result_retrieved') is not False or
        payload.get('target_result_inspected') is not False or payload.get('target_result_evaluated') is not False or
        type(payload.get('training_cutoff')) is not int or not 104<=payload['training_cutoff']<=1245 or
        payload.get('target_draw')!=payload['training_cutoff']+1):
        raise ValueError('Invalid Phase6 prospective scope or status')
    if set(payload.get('models',{}))!={'TranslationModel','ChainModel','Combined2D'}:
        raise ValueError('Three predeclared Phase6 tracks required')
    from src.models.predictive import rank_numbers
    from src.models.base import validate_ticket
    for name,track in payload['models'].items():
        scores={int(n):v for n,v in track['scores'].items()}; ranking=rank_numbers(scores)
        if track['ranking']!=ranking or track['direct_top6']!=sorted(ranking[:6]): raise ValueError('Rank mismatch')
        if track['seed']!=42 or set(track['top_k'])!=set(map(str,(6,8,10,12,15))): raise ValueError('Seed/cutoff mismatch')
        for k in (6,8,10,12,15):
            if track['top_k'][str(k)]!=ranking[:k]: raise ValueError('TopK mismatch')
        if set(track['portfolios'])!={'weighted','coverage'}: raise ValueError('Missing frozen methods')
        for group in track['portfolios'].values():
            if set(group)!=set(map(str,(1,5,10,20))): raise ValueError('Budget mismatch')
            for budget,tickets in group.items():
                if len(tickets)!=int(budget) or len(set(map(tuple,tickets)))!=len(tickets) or tickets!=group['20'][:int(budget)]:
                    raise ValueError('Invalid unique nested portfolio')
                for ticket in tickets:
                    validate_ticket(ticket)
                    if not set(ticket)<=set(ranking[:12]): raise ValueError('Ticket outside frozen pool')
    components=payload['fitted_models']
    if set(components)!={'TranslationModel','ChainModel'}: raise ValueError('Fitted rule audit missing')
    for name,item in components.items():
        if item['training_cutoff']!=payload['training_cutoff']: raise ValueError('Rule cutoff mismatch')
        expected=(TranslationModel() if name=='TranslationModel' else ChainModel()).configuration()
        if item['configuration']!=expected or payload['models'][name]['configuration']!=expected:
            raise ValueError('Predeclared model configuration changed')
    combined=combine_scores(*[{int(n):v for n,v in payload['models'][name]['scores'].items()}
                              for name in ('TranslationModel','ChainModel')])
    if any(combined[n]!=float(payload['models']['Combined2D']['scores'].get(str(n),payload['models']['Combined2D']['scores'].get(n))) for n in combined):
        raise ValueError('Combined score mismatch')


def _manifest(payload):
    lines=['# Phase 6 independent prospective experiment','',
        f"Experiment: {payload['experiment_id']}",f"Status: {payload['status']}",
        f"Target draw: {payload['target_draw']}; training cutoff: {payload['training_cutoff']}",
        f"Latest included date: {payload['latest_training_date']}",
        f"Created: {payload['created_at']}",f"Dataset SHA-256: `{payload['dataset_hash']}`",
        f"Git SHA: `{payload['git_sha']}`; dirty: {payload['git_dirty']}",
        '', 'Target result was NOT retrieved, inspected, or evaluated. No predictive advantage is claimed.',
        'This is a separate Phase6 experiment. The existing Phase5 experiment is unchanged.',
        'All configurations were predeclared; combined scores use equal average-tie percentile ranks.',
        'Fit once on all included history. No target label enters fitting or scoring.',
        'Scores express rule support, not calibrated appearance probabilities.',
        'Exact score ties use smaller number first. Portfolio seed42, Top12 pool; budgets are nested prefixes.',
        'Candidate pool hypotheses: Top8/10/12/15 contains >=3, >=4, >=5 or all6 main winners.',
        '', '## Environment', '```json',json.dumps(payload['environment'],indent=2),'```']
    for name,track in payload['models'].items():
        lines.extend(['',f'## {name}','```json',json.dumps(track['configuration'],indent=2),'```'])
        for k in (6,8,10,12,15): lines.append(f"Top{k}: {track['top_k'][str(k)]}")
        lines.extend([f"Complete ranking: {track['ranking']}",'', 'Full scores: '+json.dumps(track['scores'],sort_keys=True),
                      '',f"Direct Top6: {track['direct_top6']}"])
        for method,group in track['portfolios'].items():
            lines.append(f'### {method}, seed42')
            for budget,tickets in group.items(): lines.append(f'{budget} tickets: '+json.dumps(tickets))
    return '\n\n'.join(lines)+'\n'


def freeze_2d(source,directory,*,expected_target=1246):
    directory=Path(directory)
    if directory.resolve()==(ROOT/'reports/prospective').resolve():
        raise ValueError('Phase6 must use its own directory; Phase5 registry is immutable')
    reservation=directory/f'draw{expected_target}_phase6_2d.reservation.json'
    if reservation.exists() or any(int(r['target_draw'])==expected_target for r in registry_rows(directory)):
        raise ValueError('Phase6 target already frozen/reserved; no regeneration')
    data,dataset_hash=strict_source(source)
    if len(data)+1!=expected_target: raise ValueError('Source cutoff does not match declared target')
    if expected_target==1246 and dataset_hash!=CANONICAL_HASH: raise ValueError('Canonical hash changed; refusing freeze')
    x=lotto_matrix(data,cutoff=len(data))
    models={name:cls().fit(x,cutoff=len(x)) for name,cls in [('TranslationModel',TranslationModel),('ChainModel',ChainModel)]}
    scores={name:model.score_matrix(x,target=expected_target) for name,model in models.items()}
    scores['Combined2D']=combine_scores(scores['TranslationModel'],scores['ChainModel'])
    configs={name:model.configuration() for name,model in models.items()}
    configs['Combined2D']=dict(model='Combined2D',version='phase6-v1',components=['TranslationModel','ChainModel'],
        weights=[.5,.5],normalization='average-tie percentile rank',selection='predeclared; no outcome-dependent selection')
    now=datetime.now(timezone(timedelta(hours=9)))
    identity=f'draw{expected_target}_phase6_2d_{now.strftime("%Y%m%dT%H%M%S%f")}_{uuid4().hex[:8]}'
    code={str(p.relative_to(ROOT)):p.read_text(encoding='utf-8') for p in sorted((ROOT/'src').rglob('*.py'))}
    payload=dict(schema_version='phase6-2d-v1',phase=6,experiment_id=identity,
        target_draw=expected_target,training_cutoff=len(data),latest_training_date=str(data.iloc[-1].draw_date.date()),
        created_at=now.isoformat(),dataset_hash=dataset_hash,git_sha=_git('rev-parse','HEAD'),
        git_dirty=bool(_git('status','--porcelain')),git_status=_git('status','--short'),
        status='FROZEN_UNEVALUATED',target_result_retrieved=False,target_result_inspected=False,target_result_evaluated=False,
        seed=42,feature_version='binary-main-matrix-v1; row=draw-1,column=number-1; bonus excluded',
        protocol=(ROOT/'docs/superpowers/plans/2026-10-17-phase6.md').read_text(encoding='utf-8'),
        environment=dict(python=sys.version,platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__),
        sources=code,source_hashes={name:sha256(text.encode()).hexdigest() for name,text in code.items()},
        fitted_models={name:dict(training_cutoff=model.training_cutoff,configuration=model.configuration(),rules=model.rules) for name,model in models.items()},
        models={name:prepare_track(s,configs[name],seed=42,portfolios=True) for name,s in scores.items()})
    validate_2d(payload)
    directory.mkdir(parents=True,exist_ok=True)
    paths={key:directory/(identity+suffix) for key,suffix in [('snapshot','.json'),('manifest','_manifest.md'),('integrity','_integrity.json')]}
    with registry_lock(directory):
        if reservation.exists() or any(int(r['target_draw'])==expected_target for r in registry_rows(directory)):
            raise ValueError('Phase6 target already frozen/reserved')
        with reservation.open('x',encoding='utf-8') as stream: json.dump(dict(experiment_id=identity,target_draw=expected_target),stream)
        with paths['snapshot'].open('x',encoding='utf-8') as stream: json.dump(payload,stream,indent=2,allow_nan=False)
        with paths['manifest'].open('x',encoding='utf-8') as stream: stream.write(_manifest(payload))
        integrity={p.name:digest(p) for key,p in paths.items() if key!='integrity'}
        with paths['integrity'].open('x',encoding='utf-8') as stream: json.dump(integrity,stream,indent=2)
        registry=directory/'registry.csv'; exists=registry.exists()
        row={key:payload[key] for key in REGISTRY_FIELDS if key in payload}
        row.update(snapshot_path=paths['snapshot'].name,snapshot_hash=digest(paths['snapshot']),
            manifest_path=paths['manifest'].name,manifest_hash=digest(paths['manifest']),integrity_path=paths['integrity'].name)
        with registry.open('a',newline='',encoding='utf-8') as stream:
            writer=csv.DictWriter(stream,fieldnames=REGISTRY_FIELDS)
            if not exists: writer.writeheader()
            writer.writerow(row)
    verify_2d(paths['snapshot'])
    return paths


def verify_2d(snapshot):
    snapshot=Path(snapshot); payload=json.loads(snapshot.read_text(encoding='utf-8')); validate_2d(payload)
    identity=payload['experiment_id']
    if snapshot.name!=identity+'.json': raise ValueError('Snapshot identity mismatch')
    integrity=json.loads(snapshot.with_name(identity+'_integrity.json').read_text(encoding='utf-8'))
    names={snapshot.name,identity+'_manifest.md'}
    if set(integrity)!=names: raise ValueError('Invalid integrity members')
    for name,value in integrity.items():
        if digest(snapshot.with_name(name))!=value: raise ValueError('Phase6 artifact integrity mismatch')
    rows=[r for r in registry_rows(snapshot.parent) if r['experiment_id']==identity]
    if len(rows)!=1: raise ValueError('Missing/duplicate registry entry')
    row=rows[0]
    for field,expected in [('snapshot_path',snapshot.name),('manifest_path',identity+'_manifest.md'),('integrity_path',identity+'_integrity.json')]:
        if row[field]!=expected: raise ValueError('Registry artifact path mismatch')
    for field in ('target_draw','training_cutoff','created_at','git_sha','dataset_hash','status'):
        if row[field]!=str(payload[field]): raise ValueError('Registry metadata mismatch')
    if row['snapshot_hash']!=digest(snapshot) or row['manifest_hash']!=integrity[identity+'_manifest.md']:
        raise ValueError('Registry integrity mismatch')
    for name,source in payload['sources'].items():
        if sha256(source.encode()).hexdigest()!=payload['source_hashes'][name]: raise ValueError('Embedded source integrity mismatch')
    return payload
