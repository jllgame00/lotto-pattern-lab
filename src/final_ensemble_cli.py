"""H17 staged historical research and configuration-only records. No publication."""
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import numpy as np
import pandas as pd
from .optimal_transport_cli import load_source
from .randomness_cli import verified_archive
from .random_matrix_cli import dump
from .analysis.final_ensemble_inputs import replay,load_panel,canonical_configs
from .analysis.final_ensemble import (PROMOTED,SPLITS,templates,split_panel,select_development,
    validate_selection,combine_ranks,metrics,metric_series,diversity,paired_interval,leave_one_out,run_placebos)

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'reports/final_ensemble'
SCIENTIFIC_FILES=['src/analysis/final_ensemble.py','src/analysis/final_ensemble_inputs.py','src/analysis/final_ensemble_portfolio.py','src/final_ensemble_cli.py']


def digest(payload):return sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def write_seal(path,payload):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(dict(payload=payload,sha256=digest(payload)),f,ensure_ascii=False,allow_nan=False,indent=2);f.write('\n')


def read_seal(path):
    record=json.loads(Path(path).read_text(encoding='utf-8'))
    if digest(record['payload'])!=record['sha256']:raise ValueError('Immutable stage hash mismatch')
    return record['payload']


def guard(path):
    path=Path(path).resolve()
    if not path.is_relative_to(DIRECTORY.resolve()):raise ValueError('H17 outputs restricted to repository reports/final_ensemble')
    path.mkdir(parents=True,exist_ok=True);return path


def begin_final(directory,validation_hash):
    write_seal(Path(directory)/'final_started.json',dict(validation_hash=validation_hash,
        final_start=1131,final_end=1245,model_selection_evaluations=1))


def configuration_record(gate,status,*,git_sha,data_sha,archive_status):
    if archive_status!='VERIFIED':raise ValueError('Verified unchanged prospective archive required')
    ready=gate['passed'] and status in ('EXPLORATORY_ENSEMBLE_CANDIDATE','HISTORICAL_ENSEMBLE_ADVANTAGE')
    return dict(version='h17-configuration-v1',kind='CONFIGURATION_ONLY',historical_status=status,
        readiness='H17_CONFIGURATION_FROZEN_READY_FOR_1247' if ready else 'H17_CONFIGURATION_FROZEN_NOT_CURRENTLY_JUSTIFIED',
        ready_for_1247=bool(ready),intended_future_target=1247,historical_selection_cutoff=1245,
        candidates=list(PROMOTED),underlying_configurations={n:canonical_configs()[n] for n in PROMOTED},
        selected=gate['selected'],best_single=gate['best_single'],validation_passed=gate['passed'],
        rank_rule='(rank-1)/44; weighted mean rounded12decimals; lower better; ties smaller number',
        ticket_rules=dict(pool_size=12,budgets=[1,5,10,20],methods=['weighted','coverage'],
            score='(46-rank)/45',construction='existing make_portfolio;20unique tickets then budget prefixes',
            seed=270500,seed_formula='SeedSequence([270500,replicate,target])',replicates=10),
        seeds=dict(model=42,bootstrap=270042,random_weights=270101,random_candidates=270202),
        prospective_refit_rule='Only after explicit verified1246 import: refit all frozen components on entire1..1246; no design changes',
        git_sha=git_sha,data_sha256=data_sha,archive_status=archive_status,draw1246_used=False,
        draw1247_prediction_generated=False,publication_executed=False)


def prepare(directory):
    start=json.loads((directory/'starting_state.json').read_text(encoding='utf-8'))
    if verified_archive(ROOT/'reports/prospective')!=start['archive']:raise ValueError('Prospective archive changed')
    plan=(ROOT/'docs/superpowers/plans/2026-10-18-phase27.md').read_bytes()
    with (directory/'predeclared_plan.md').open('xb') as f:f.write(plan)
    ledger=json.loads((ROOT/'docs/weak-signal-candidates.json').read_text(encoding='utf-8'))
    dump(directory/'provenance_before.json',ledger)
    import scipy
    payload=dict(version='h17-v1',historical_cutoff=1245,common=[901,1245],splits=SPLITS,
        candidates=list(PROMOTED),audit_only=['MutualInformationModel'],configs=canonical_configs(),
        grid=templates(PROMOTED),primary='ensemble meanwinningrank;Top6secondary',diversity_penalty=.02,
        validation='one devwinner;strictMWRbetterthanGap/bestsingle/equalall;Top6no-worse;no runnerup',
        fallback='equalall audit baseline, no promotion after failed gate',stacking=False,
        placebos=199,placebo_tail_threshold_each=.025,placebo_inference='selection diagnostics, not calibrated global p-values',
        bootstrap=2000,blocks=[26,13,52],portfolio_seeds=10,protected_inventory_hash=digest(start['protected']),
        plan_sha256=sha256(plan).hexdigest(),source_hashes={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in SCIENTIFIC_FILES},
        start_sha=start['head'],data_sha256=start['data_sha256'],
        environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,pandas=pd.__version__),
        hindsight='Retrospective; all901..1245 previously inspected; not pristine validation')
    write_seal(directory/'protocol.json',payload);print('H17 protocol frozen;47weight cells/11equal subsets',flush=True)


def protocol(directory):
    p=read_seal(directory/'protocol.json')
    start=json.loads((directory/'starting_state.json').read_text())
    if digest(start['protected'])!=p['protected_inventory_hash']:raise ValueError('Starting inventory changed')
    for name,h in start['protected'].items():
        if sha256((ROOT/name).read_bytes()).hexdigest()!=h:raise ValueError('Protected dependency changed: '+name)
    for name,h in p['source_hashes'].items():
        if sha256((ROOT/name).read_bytes()).hexdigest()!=h:raise ValueError('Scientific source changed after protocol freeze: '+name)
    if sha256((ROOT/'data/raw/lotto_history.csv').read_bytes()).hexdigest()!=p['data_sha256']:raise ValueError('Data changed')
    return p


def reproduce(history,directory,*,cadence=26):
    protocol(directory);path=directory/f'predictions_{cadence}.csv'
    if path.exists():raise FileExistsError('Replay evidence already exists')
    rows=replay(history,cadence=cadence,progress=lambda s:print(s,flush=True));rows.to_csv(path,index=False)
    expected={'RandomModel':[149,135,53,8,0,0,0],'Frequency26':[142,144,54,5,0,0,0],
        'GapLogistic':[141,135,55,13,1,0,0],'GraphStructureModel':[129,144,64,8,0,0,0],
        'GapShapeModel':[139,136,58,11,1,0,0],'MirrorModel':[138,143,52,10,2,0,0],
        'MutualInformationModel':[134,140,62,9,0,0,0]}
    checks=[]
    for name,g in rows.groupby('model'):
        counts=np.bincount(g.hits,minlength=7).tolist()
        checks.append(dict(model=name,observed=counts,documented=expected[name],matches=counts==expected[name]))
    dump(directory/f'replay_audit_{cadence}.json',dict(cadence=cadence,anchor=901,checks=checks,
        original_bytes_verified=False,provenance='new exact-config causal replay, old artifacts remain unavailable',
        csv_sha256=sha256(path.read_bytes()).hexdigest()))
    if cadence==26 and not all(c['matches'] for c in checks):raise ValueError('Documented replay mismatch; stop before selection')
    print(f'Replay{cadence} saved;{len(rows)}causal prediction rows',flush=True)


def panels(directory,*,cadence=26):
    protocol(directory);audit=json.loads((directory/f'replay_audit_{cadence}.json').read_text())
    if cadence==26 and (len(audit['checks'])!=7 or {row.get('model') for row in audit['checks']}!=set(canonical_configs()) or not all(row['matches'] for row in audit['checks'])):
        raise ValueError('Failed replay audit; selection prohibited')
    path=directory/f'predictions_{cadence}.csv'
    if sha256(path.read_bytes()).hexdigest()!=audit['csv_sha256']:raise ValueError('Prediction artifact hash mismatch')
    rows=pd.read_csv(path,float_precision='round_trip')
    allnames=[*PROMOTED,'MutualInformationModel','RandomModel','Frequency26']
    p=load_panel(rows,allnames)
    if p['targets'].tolist()!=list(range(901,1246)):raise ValueError('Exact common345targets required')
    selected=dict(p,names=list(PROMOTED),ranks=p['ranks'][:,:4])
    return selected,p


def develop(directory):
    p,_=panels(directory);s=select_development(split_panel(p,'development'))
    s.update(protocol_hash=digest(protocol(directory)),prediction_sha256=sha256((directory/'predictions_26.csv').read_bytes()).hexdigest())
    write_seal(directory/'development_selection.json',s)
    pd.DataFrame(s['development_rows']).to_csv(directory/'development_grid.csv',index=False)
    print('Development frozen:',s['winner']['id'],'best single:',s['best_single'],flush=True)


def validate(directory):
    p,_=panels(directory);s=read_seal(directory/'development_selection.json')
    gate=validate_selection(split_panel(p,'validation'),s)
    gate.update(development_hash=digest(s),protocol_hash=digest(protocol(directory)))
    write_seal(directory/'validation_gate.json',gate)
    print('Validation gate:',gate['passed'],'selected:',gate['selected']['id'],flush=True)


def evaluated_ranks(panel,allpanel,selection,gate):
    ranks={name:allpanel['ranks'][:,i] for i,name in enumerate(allpanel['names'])}
    for name,spec in [('EqualAll',templates(PROMOTED)[-1]),('OrdinarySubset',selection['ordinary']),
        ('DiversitySubset',selection['diversity']),('WeightedWinner',selection['winner']),('SelectedEnsemble',gate['selected'])]:
        ranks[name]=combine_ranks(panel['ranks'],spec['weights'])
    return ranks


def final_evaluation(history,directory):
    p,allp=panels(directory);s=read_seal(directory/'development_selection.json');gate=read_seal(directory/'validation_gate.json')
    begin_final(directory,digest(gate))
    ranks=evaluated_ranks(p,allp,s,gate);performance=[];paired=[];robust=[];loo=[];corr=[]
    for scope,(a,b) in SPLITS.items():
        mask=(p['targets']>=a)&(p['targets']<=b);actual=p['actual'][mask]
        for name,r in ranks.items():performance.append(dict(scope=scope,model=name,**metrics(r[mask],actual)))
        for row in leave_one_out(split_panel(p,scope),gate['selected']['weights']):loo.append(dict(scope=scope,**row))
        dp=dict(targets=p['targets'][mask],ranks=allp['ranks'][mask,:5],actual=actual,names=allp['names'][:5])
        corr.extend(dict(scope=scope,**row) for row in diversity(dp))
        if scope in ('validation','final'):
            candidate=metric_series(ranks['SelectedEnsemble'][mask],actual)
            for ref in dict.fromkeys(['RandomModel','GapLogistic',s['best_single']]):
                reference=metric_series(ranks[ref][mask],actual)
                for block in (26,13,52):
                    paired.append(dict(scope=scope,reference=ref,metric='mean_winning_rank_improvement',
                        **paired_interval(reference['mean_winning_rank'],candidate['mean_winning_rank'],block=block)))
                    paired.append(dict(scope=scope,reference=ref,metric='top6_improvement',
                        **paired_interval(candidate['hits'],reference['hits'],block=block)))
    corr.extend(dict(scope='common',**row) for row in diversity(dict(allp,names=allp['names'][:5],ranks=allp['ranks'][:,:5])))
    for start in (1131,1170,1208):
        mask=p['targets']>=start
        for name in dict.fromkeys(['SelectedEnsemble','GapLogistic',s['best_single']]):
            robust.append(dict(start=start,end=1245,cadence=26,model=name,**metrics(ranks[name][mask],p['actual'][mask])))
    for name,rows in [('performance',performance),('paired',paired),('robustness',robust),('leave_one_out',loo),('diversity',corr)]:
        pd.DataFrame(rows).to_csv(directory/f'{name}.csv',index=False)
    np.savez_compressed(directory/'frozen_rankings.npz',targets=p['targets'],actual=p['actual'],**ranks)
    # Fixed target examples, no outcome-driven example selection.
    examples=[]
    for target in (1131,1188,1245):
        i=int(target-901)
        for n in range(45):
            row=dict(target_draw=target,number=n+1,actual=bool(p['actual'][i,n]),ensemble_rank=int(ranks['SelectedEnsemble'][i,n]),
                disagreement_std=float(p['ranks'][i,:,n].std()))
            for c,name in enumerate(PROMOTED):
                row[name+'_rank']=int(p['ranks'][i,c,n]);row[name+'_contribution']=float(gate['selected']['weights'][c]*(p['ranks'][i,c,n]-1)/44)
            examples.append(row)
    pd.DataFrame(examples).to_csv(directory/'interpretability.csv',index=False)
    final=[r for r in performance if r['scope']=='final'];print('Frozen final audit complete',flush=True)
    dump(directory/'final_evaluation.json',dict(final=final,validation_gate=gate['passed'],configuration=gate['selected'],
        best_single=s['best_single'],selection_reruns=0,draw1246_used=False))


def robustness(history,directory):
    read_seal(directory/'final_started.json')
    if (directory/'placebos.csv').exists():raise FileExistsError('Robustness evidence already exists')
    p,allp=panels(directory);s=read_seal(directory/'development_selection.json');gate=read_seal(directory/'validation_gate.json')
    placebo=run_placebos(p,progress=lambda msg:print(msg,flush=True));pd.DataFrame(placebo).to_csv(directory/'placebos.csv',index=False)
    reproduce(history,directory,cadence=13);p13,all13=panels(directory,cadence=13)
    r13=evaluated_ranks(p13,all13,s,gate);rows=[]
    for scope,(a,b) in SPLITS.items():
        mask=(p13['targets']>=a)&(p13['targets']<=b)
        for name in dict.fromkeys(['SelectedEnsemble','GapLogistic',s['best_single']]):rows.append(dict(scope=scope,model=name,cadence=13,**metrics(r13[name][mask],p13['actual'][mask])))
    pd.DataFrame(rows).to_csv(directory/'cadence_robustness.csv',index=False)
    from .analysis.final_ensemble_portfolio import evaluate_portfolios
    with np.load(directory/'frozen_rankings.npz') as f:
        mask=f['targets']>=1131
        order={label:np.argsort(f[name][mask],axis=1)+1 for label,name in [('SelectedEnsemble','SelectedEnsemble'),('GapLogistic','GapLogistic'),('BestSingle',s['best_single'])]}
        portfolio=evaluate_portfolios(order,f['targets'][mask],f['actual'][mask],history.set_index('draw_no').loc[f['targets'][mask],'bonus'].to_numpy())
    for name in ('draws','summary'):portfolio[name].to_csv(directory/f'portfolio_{name}.csv',index=False)
    dump(directory/'portfolio_configuration.json',portfolio['config']);print('Robustness/placebos/portfolios complete',flush=True)


def placebo_comparison(table,*,real_gain,gate_passed):
    promoted=real_gain if gate_passed else 0.
    raw={};promotion={}
    for kind,group in table.groupby('kind'):
        raw[kind]=(1+int(np.sum(group.final_rank_gain>=real_gain)))/(len(group)+1)
        promotion[kind]=(1+int(np.sum(group.final_promoted_gain>=promoted)))/(len(group)+1) if gate_passed else None
    return dict(observed_promoted_gain=promoted,raw_tail_fractions=raw,promotion_tail_fractions=promotion,
        interpretation='Selection diagnostics, not calibrated frequentist p-values; no promotion inference after failed real gate')


def validate_completion(performance,paired,placebos,best_single):
    models=set(canonical_configs())|{'EqualAll','OrdinarySubset','DiversitySubset','WeightedWinner','SelectedEnsemble'}
    refs=set(['RandomModel','GapLogistic',best_single]);scopes={'validation','final'}
    wanted={(s,r,m,b) for s in scopes for r in refs for m in ('mean_winning_rank_improvement','top6_improvement') for b in (26,13,52)}
    if (not {'scope','model','targets','avg_top6','mean_winning_rank'}<=set(performance) or
            len(performance)!=3*len(models) or performance.duplicated(['scope','model']).any() or
            set(zip(performance.scope,performance.model))!={(s,m) for s in SPLITS for m in models} or
            not performance.targets.eq(115).all() or not np.isfinite(performance[['avg_top6','mean_winning_rank']]).all().all()):
        raise ValueError('Incomplete final performance evidence')
    if (not {'scope','reference','metric','block','difference','ci_low','simultaneous_low'}<=set(paired) or
            len(paired)!=len(wanted) or set(zip(paired.scope,paired.reference,paired.metric,paired.block))!=wanted or
            not np.isfinite(paired[['difference','ci_low','simultaneous_low']]).all().all()):
        raise ValueError('Incomplete paired evidence')
    if (not {'kind','replicate','final_rank_gain','final_promoted_gain','gate_passed'}<=set(placebos) or len(placebos)!=398 or
            set(zip(placebos.kind,placebos.replicate))!={(k,i) for k in ('random_weight','random_candidate') for i in range(199)} or
            not np.isfinite(placebos[['final_rank_gain','final_promoted_gain']]).all().all()):
        raise ValueError('Incomplete placebo evidence')


def finish(directory):
    p,allp=panels(directory);s=read_seal(directory/'development_selection.json');gate=read_seal(directory/'validation_gate.json')
    perf=pd.read_csv(directory/'performance.csv');pairs=pd.read_csv(directory/'paired.csv');placebo=pd.read_csv(directory/'placebos.csv')
    validate_completion(perf,pairs,placebo,s['best_single'])
    final=perf[perf.scope=='final'].set_index('model');a=final.loc['SelectedEnsemble'];b=final.loc[s['best_single']]
    gains={ref:float(final.loc[ref].mean_winning_rank-a.mean_winning_rank) for ref in dict.fromkeys(['RandomModel','GapLogistic',s['best_single']])}
    placebo_result=placebo_comparison(placebo,real_gain=gains[s['best_single']],gate_passed=gate['passed'])
    placebo_tail=placebo_result['promotion_tail_fractions']
    point=all(gains[ref]>0 and a.avg_top6>=final.loc[ref].avg_top6 for ref in ('GapLogistic',s['best_single']))
    robust=pd.read_csv(directory/'robustness.csv');cadence=pd.read_csv(directory/'cadence_robustness.csv')
    robust_ok=True
    for _,part in robust.groupby('start'):
        means=part.groupby('model').mean_winning_rank.first();robust_ok &= all(means.SelectedEnsemble<=means[ref] for ref in ('GapLogistic',s['best_single']))
    c=cadence[cadence.scope=='final'].groupby('model').mean_winning_rank.first()
    robust_ok &= all(c.SelectedEnsemble<=c[ref] for ref in ('GapLogistic',s['best_single']))
    primary=pairs[(pairs.scope=='final')&(pairs.block==26)&(pairs.metric=='mean_winning_rank_improvement')]
    supported=bool((primary.simultaneous_low>0).all())
    status='NO_ENSEMBLE_ADVANTAGE_ESTABLISHED'
    if gate['passed'] and point:
        status='EXPLORATORY_ENSEMBLE_CANDIDATE'
        if supported and robust_ok and all(v<=.025 for v in placebo_tail.values()):status='HISTORICAL_ENSEMBLE_ADVANTAGE'
    summary=dict(status=status,selected=gate['selected'],best_single=s['best_single'],validation_passed=gate['passed'],
        selected_final_rank_gain=gains[s['best_single']],rank_gains=gains,placebo_comparison=placebo_result,
        placebo_gate_rates={kind:float(group.gate_passed.mean()) for kind,group in placebo.groupby('kind')},
        final_point_gate=bool(point),simultaneous_primary_supported=supported,robustness_supported=bool(robust_ok),
        historical_cutoff=1245,common=[901,1245],splits=SPLITS,draw1246_used=False,draw1247_prediction_generated=False)
    dump(directory/'main_summary.json',summary)
    start=json.loads((directory/'starting_state.json').read_text());archive=verified_archive(ROOT/'reports/prospective')
    if archive!=start['archive']:raise ValueError('Archive changed')
    config=configuration_record(gate,status,git_sha=start['head'],data_sha=start['data_sha256'],archive_status=archive['status'])
    config.update(protocol_hash=digest(read_seal(directory/'protocol.json')),development_hash=digest(s),validation_hash=digest(gate),
        scientific_source_hashes=protocol(directory)['source_hashes'])
    write_seal(directory/'configuration_freeze.json',config)
    print(status,config['readiness'],flush=True)


def add_commands(commands):
    p=commands.add_parser('final-ensemble',help='H17 bounded historical research/config-only freeze')
    p.add_argument('action',choices=['prepare','replay','develop','validate','evaluate','robustness','finish','plots','audit'])
    p.add_argument('--reports-dir',type=Path,default=DIRECTORY)


def run(args):
    d=guard(args.reports_dir)
    if args.action=='prepare':prepare(d);return
    history,x=load_source(args.data)
    if args.action=='replay':reproduce(history,d)
    elif args.action=='develop':develop(d)
    elif args.action=='validate':validate(d)
    elif args.action=='evaluate':final_evaluation(history,d)
    elif args.action=='robustness':robustness(history,d)
    elif args.action=='finish':finish(d)
    elif args.action=='plots':
        from .analysis.final_ensemble_plots import diagnostics
        diagnostics(d)
    elif args.action=='audit':
        from .analysis.final_ensemble_audit import audit
        audit(history,d)
