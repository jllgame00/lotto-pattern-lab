"""Version2 immutable prediction artifacts and append-only experiment registry."""
from contextlib import contextmanager
import csv
from hashlib import sha256
import json
from pathlib import Path
import re

import numpy as np
from src.models.predictive import _scores, rank_numbers
from src.models.base import validate_ticket
from src.backtest.portfolios import make_portfolio, uniform_portfolio

TRACKS={'GapLogistic','BayesianStatic','HMM2','HMM3','Ensemble','UniformRandom'}
BUDGETS=(1,5,10,20)
REGISTRY_FIELDS=['experiment_id','target_draw','training_cutoff','created_at','git_sha','dataset_hash',
                 'snapshot_path','snapshot_hash','manifest_path','manifest_hash','integrity_path','status']


def digest(path): return sha256(Path(path).read_bytes()).hexdigest()


def prepare_track(scores,configuration,*,seed=42,portfolios=False,uniform=False):
    values=_scores(scores)
    configuration=json.loads(json.dumps(configuration,allow_nan=False))
    ranking=np.random.default_rng(seed).permutation(np.arange(1,46)).tolist() if uniform else rank_numbers(scores)
    ties=[[n for n in range(1,46) if scores[n]==value] for value in sorted(set(values),reverse=True)]
    record=dict(scores=scores,ranking=ranking,top_k={str(k):ranking[:k] for k in (6,8,10,12,15)},
        direct_top6=sorted(ranking[:6]),tie_groups=[group for group in ties if len(group)>1],
        tie_breaking='numpy seeded uniform permutation of all45 equal scores' if uniform else 'descending score; exact ties smaller number first',
        configuration=configuration,seed=seed,portfolios={},candidate_pool_size=45 if uniform else 12)
    if uniform:
        if not np.all(values==values[0]): raise ValueError('Uniform ranking requires tied scores')
        tickets=uniform_portfolio(20,seed=seed)
        record['portfolios']['uniform']={str(b):tickets[:b] for b in BUDGETS}
    elif portfolios:
        for method in ('weighted','coverage'):
            tickets=make_portfolio(scores,ranking[:12],budget=20,method=method,seed=seed)
            record['portfolios'][method]={str(b):tickets[:b] for b in BUDGETS}
    return record


def validate_snapshot(payload):
    try: _validate_snapshot(payload)
    except (KeyError,TypeError,AttributeError) as exc: raise ValueError('Malformed frozen snapshot schema') from exc


def _validate_snapshot(payload):
    if (payload.get('schema_version')!=2 or payload.get('status')!='FROZEN_UNEVALUATED' or
        type(payload.get('training_cutoff')) is not int or
        payload.get('target_draw')!=payload['training_cutoff']+1 or
        payload.get('target_result_retrieved') is not False or payload.get('target_result_inspected') is not False):
        raise ValueError('Invalid prospective cutoff/status or target-result declaration')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',payload.get('experiment_id','')):
        raise ValueError('Invalid experiment identifier')
    if set(payload.get('models',{}))!=TRACKS: raise ValueError('Exactly six declared model tracks required')
    from src.freeze_validation import validate_provenance
    validate_provenance(payload)
    for name,model in payload['models'].items():
        scores={int(k):v for k,v in model['scores'].items()}; _scores(scores)
        ranking=model['ranking']
        if len(ranking)!=45 or any(type(n) is not int for n in ranking) or set(ranking)!=set(range(1,46)):
            raise ValueError('Full ranking must contain45 unique numbers')
        uniform=name=='UniformRandom'
        if model['seed']!=42: raise ValueError('Phase5 fixes seed42 before prediction')
        if uniform:
            if not np.allclose(list(scores.values()),6/45,rtol=0,atol=0): raise ValueError('Uniform control requires fair tied scores')
        elif ranking!=sorted(scores,key=lambda n:(-scores[n],n)):
            raise ValueError('Ranking disagrees with frozen scores/tie rule')
        for k in (6,8,10,12,15):
            if model['top_k'].get(str(k))!=ranking[:k]: raise ValueError('TopK disagrees with full ranking')
        if set(model['top_k'])!=set(map(str,(6,8,10,12,15))) or model['direct_top6']!=sorted(ranking[:6]):
            raise ValueError('Missing cutoffs or inconsistent direct ticket')
        ties=[[n for n in range(1,46) if scores[n]==v] for v in sorted(set(scores.values()),reverse=True)]
        if model['tie_groups']!=[group for group in ties if len(group)>1]: raise ValueError('Tie groups inconsistent')
        expected_rule='numpy seeded uniform permutation of all45 equal scores' if uniform else 'descending score; exact ties smaller number first'
        if model['tie_breaking']!=expected_rule or model['candidate_pool_size']!=(45 if uniform else 12):
            raise ValueError('Tie rule/pool mismatch')
        methods={'uniform'} if uniform else {'weighted','coverage'} if name in ('GapLogistic','Ensemble') else set()
        if set(model['portfolios'])!=methods: raise ValueError('Declared portfolio methods missing or altered')
        for group in model['portfolios'].values():
            if set(group)!=set(map(str,BUDGETS)): raise ValueError('Budget mismatch')
            for budget,tickets in group.items():
                if len(tickets)!=int(budget) or len(set(map(tuple,tickets)))!=len(tickets):
                    raise ValueError('Duplicate ticket or wrong budget')
                if tickets!=group['20'][:int(budget)]: raise ValueError('Portfolio budgets must be nested prefixes')
                for ticket in tickets:
                    validate_ticket(ticket)
                    if not uniform and not set(ticket)<=set(ranking[:12]): raise ValueError('Ticket outside frozen Top12')


def registry_rows(directory):
    path=Path(directory)/'registry.csv'
    if not path.exists(): return []
    with path.open(newline='',encoding='utf-8') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=REGISTRY_FIELDS: raise ValueError('Unexpected registry schema; will not overwrite')
        return list(reader)


def ensure_unfrozen(directory,target):
    if (Path(directory)/f'draw_{target}.reservation.json').exists():
        raise ValueError(f'Target{target} already reserved; no retry may create a replacement experiment')
    if any(int(row['target_draw'])==target for row in registry_rows(directory)):
        raise ValueError(f'Target{target} already frozen; original experiment must remain unchanged')


@contextmanager
def registry_lock(directory):
    lock=Path(directory)/'.registry.lock'
    try: stream=lock.open('x',encoding='utf-8')
    except FileExistsError as exc: raise ValueError('Registry is locked; no concurrent or stale-lock overwrite allowed') from exc
    try:
        stream.write('Exclusive prospective artifact publication\n'); stream.close()
        yield
    finally:
        stream.close(); lock.unlink()


def manifest_text(payload):
    lines=[f'# Frozen Lotto experiment: draw {payload["target_draw"]}', '',
        f'- Experiment: `{payload["experiment_id"]}`',
        f'- Status: **{payload["status"]}**',
        f'- Target draw: **{payload["target_draw"]}**',
        f'- Training cutoff: **{payload["training_cutoff"]}**; allowed source draws1-{payload["training_cutoff"]}',
        f'- Latest training date: {payload["latest_training_date"]}',
        f'- Generated: {payload["created_at"]}',
        f'- Dataset SHA-256: `{payload["canonical_dataset_sha256"]}`',
        f'- Git SHA: `{payload.get("git_commit")}`; dirty: `{payload.get("git_dirty")}`', '',
        f'Draw {payload["target_draw"]} was not retrieved or inspected. No future result is present.',
        'This is an experimental freeze, not a predictive or profitability claim. Local hashes',
        'detect changes against the saved integrity record; they are not a trusted external timestamp.', '',
        'The earlier draw1245 was accessed in prior research and is not a pristine holdout.', '',
        '## Protocol and environment', '', '```json',
        json.dumps({key:payload.get(key) for key in ('protocol','environment','feature_definitions','ensemble_source')},indent=2),
        '```', '', '## Frozen tracks', '']
    for name,model in payload['models'].items():
        lines += [f'### {name}', '', f'Tie rule: {model["tie_breaking"]}. Seed: {model["seed"]}.',
            f'Exact tied groups: {model["tie_groups"] or "none"}', '', 'Configuration:', '```json',
            json.dumps(model['configuration'],indent=2), '```', '',
            f'Complete rank1-45: {model["ranking"]}', '']
        lines += [f'- Top{k}: {numbers}' for k,numbers in model['top_k'].items()]
        lines += ['', f'Direct Top6 ticket: {model["direct_top6"]}', '', '| Number | Score | Rank |', '|---|---:|---:|']
        for n in range(1,46):
            score=model['scores'].get(n,model['scores'].get(str(n)))
            lines.append(f'|{n}|{score:.17g}|{model["ranking"].index(n)+1}|')
        for method,budgets in model['portfolios'].items():
            lines += ['', f'#### {method} portfolio', '',
                'Budgets1/5/10/20 use exactly the first1/5/10/20 rows below; no alternatives were selected.', '',
                '| Ticket | Six numbers |', '|---:|---|']
            lines += [f'|{i}|{ticket}|' for i,ticket in enumerate(budgets['20'],1)]
        lines.append('')
    lines += ['## Predeclared candidate hypotheses', '',
        'For GapLogistic and Ensemble, evaluate each Top8/10/12/15 pool for the number',
        'of main winners and indicators>=3,>=4,>=5,all6. Preserve all cutoffs, including',
        'unsuccessful ones. Report equal-budget comparisons with the frozen uniform',
        'control. Bonus is used only by the later evaluator for prize classification.', '',
        'Never replace this experiment. Future changes require a separate version/experiment.', '']
    return '\n'.join(lines)


def publish_freeze(payload,directory):
    validate_snapshot(payload)
    root=Path(directory).resolve(); root.mkdir(parents=True,exist_ok=True)
    identifier=payload['experiment_id']
    paths={name:root/f'{identifier}{suffix}' for name,suffix in
           [('snapshot','.json'),('manifest','_manifest.md'),('integrity','_integrity.json')]}
    with registry_lock(root):
        ensure_unfrozen(root,payload['target_draw'])
        if any(path.exists() for path in paths.values()): raise ValueError('Artifact exists; never overwrite')
        # Persistent reservation intentionally survives every failure. Recovery
        # must use the original experiment, never silently generate a new one.
        with (root/f'draw_{payload["target_draw"]}.reservation.json').open('x',encoding='utf-8') as stream:
            json.dump(dict(experiment_id=identifier,target_draw=payload['target_draw'],
                training_cutoff=payload['training_cutoff'],created_at=payload['created_at']),stream)
        with paths['snapshot'].open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(payload,stream,indent=2,allow_nan=False); stream.write('\n')
        with paths['manifest'].open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(manifest_text(payload))
        integrity=dict(experiment_id=identifier,target_draw=payload['target_draw'],training_cutoff=payload['training_cutoff'],
            created_at=payload['created_at'],algorithm='SHA-256',
            files={paths[name].name:digest(paths[name]) for name in ('snapshot','manifest')})
        with paths['integrity'].open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(integrity,stream,indent=2); stream.write('\n')
        registry=root/'registry.csv'; new=not registry.exists()
        row=dict(experiment_id=identifier,target_draw=payload['target_draw'],training_cutoff=payload['training_cutoff'],
            created_at=payload['created_at'],git_sha=payload.get('git_commit'),dataset_hash=payload['canonical_dataset_sha256'],
            snapshot_path=paths['snapshot'].name,snapshot_hash=digest(paths['snapshot']),
            manifest_path=paths['manifest'].name,manifest_hash=digest(paths['manifest']),
            integrity_path=paths['integrity'].name,status='FROZEN_UNEVALUATED')
        with registry.open('a',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=REGISTRY_FIELDS)
            if new: writer.writeheader()
            writer.writerow(row)
    return paths


def verify_freeze(snapshot):
    snapshot=Path(snapshot).resolve()
    integrity_path=snapshot.with_name(snapshot.stem+'_integrity.json')
    integrity=json.loads(integrity_path.read_text(encoding='utf-8'))
    expected_files={snapshot.name,snapshot.stem+'_manifest.md'}
    if integrity.get('algorithm')!='SHA-256' or set(integrity.get('files',{}))!=expected_files:
        raise ValueError('Invalid integrity record')
    for name,expected in integrity['files'].items():
        path=snapshot.parent/name
        if not path.is_file() or digest(path)!=expected: raise ValueError('Artifact integrity mismatch')
    payload=json.loads(snapshot.read_text(encoding='utf-8'))
    if any(integrity.get(k)!=payload.get(k) for k in ('experiment_id','target_draw','training_cutoff','created_at')):
        raise ValueError('Integrity metadata mismatch')
    rows=[r for r in registry_rows(snapshot.parent) if r['experiment_id']==payload['experiment_id']]
    if len(rows)!=1 or rows[0]['snapshot_hash']!=digest(snapshot) or rows[0]['manifest_hash']!=digest(snapshot.parent/(snapshot.stem+'_manifest.md')):
        raise ValueError('Registry integrity mismatch')
    expected=dict(target_draw=str(payload['target_draw']),training_cutoff=str(payload['training_cutoff']),
        snapshot_path=snapshot.name,manifest_path=snapshot.stem+'_manifest.md',integrity_path=integrity_path.name,
        dataset_hash=payload['canonical_dataset_sha256'],status='FROZEN_UNEVALUATED',created_at=payload['created_at'],
        git_sha=payload.get('git_commit') or '')
    if any(rows[0][key]!=value for key,value in expected.items()): raise ValueError('Registry metadata integrity mismatch')
    validate_snapshot(payload)
    return payload
