"""Chronological expanding fits; ranking metrics and paired uncertainty."""
from __future__ import annotations

import json
import math
from time import perf_counter

import numpy as np
import pandas as pd

from src.collect.dataset import MAIN_COLUMNS, validate_history
from src.models.predictive import rank_numbers, weighted_ticket
from src.models.random_model import RandomModel


def rank_metrics(ranking, actual):
    if len(ranking)!=45 or set(ranking)!=set(range(1,46)) or len(set(actual))!=6:
        raise ValueError('Expected a complete ranking and six actual main numbers')
    ranks = {number:i+1 for i,number in enumerate(ranking)}
    winning_ranks = np.array([ranks[n] for n in actual])
    return dict(hits=int((winning_ranks<=6).sum()),mean_winning_rank=float(winning_ranks.mean()),
                **{f'recall_{k}':float((winning_ranks<=k).mean()) for k in (6,10,15)})


def _seed(seed, target, stream):
    return int(np.random.SeedSequence([seed,target,stream]).generate_state(1)[0])


def evaluate(history, features, factories, *, start=601, end=None, cadence=26,
             seed=42, tickets=0, audit=True, progress=None):
    """features must come from build_features; no external arbitrary CSV cache.

    Latest observed draw is always reserved. Each fitted instance sees only
    labels through its fit cutoff; scoring receives no label column. Between
    fits current features update, but scalers/neighbor sets remain frozen.
    """
    data = validate_history(history)
    end = len(data)-1 if end is None else end
    if (not isinstance(cadence,int) or cadence<1 or not isinstance(tickets,int) or tickets<0 or
            not isinstance(start,int) or not isinstance(end,int) or start>end or end>=len(data)):
        raise ValueError('Invalid protocol; latest draw must remain reserved')
    if features.duplicated(['target_draw','number']).any() or not features.feature_cutoff.eq(features.target_draw-1).all():
        raise ValueError('Invalid canonical feature table')
    if 'RandomModel' in factories:
        raise ValueError('RandomModel baseline is added automatically')
    train = features[(features.target_draw < start) & features.appeared_next.notna()]
    if train.empty:
        raise ValueError('No labeled feature rows before evaluation start')
    targets = list(range(start,end+1))
    batches = {int(t):g.drop(columns='appeared_next').copy() for t,g in features.groupby('target_draw') if t in targets}
    if set(batches)!=set(targets): raise ValueError('Missing target feature rows')
    results, importances = [], []
    configurations, runtimes = {}, {}
    for name,factory in [('RandomModel',None),*factories.items()]:
        began = perf_counter()
        model = None
        for index,target in enumerate(targets):
            current = batches[target].copy(deep=True)
            if len(current)!=45 or set(current.number)!=set(range(1,46)):
                raise ValueError('Every target needs 45 unique feature rows')
            target_seed = _seed(seed,target,10)
            if factory is None:
                scores = RandomModel().score_numbers(None)
                chosen = RandomModel().predict(None,seed=target_seed)
                rng = np.random.default_rng(target_seed)
                # Random ties for baseline only; within top6 randomize ranks too.
                ranking = rng.permutation(chosen).tolist()+rng.permutation([n for n in range(1,46) if n not in chosen]).tolist()
                cutoff = target-1
                config = dict(seed=seed,ticket_seed=target_seed,ties='uniform_random')
            else:
                if index % cadence == 0:
                    training = features[(features.target_draw<target) & features.appeared_next.notna()].copy(deep=True)
                    model = factory().fit(training,cutoff=target-1)
                    for item in model.importance():
                        importances.append(dict(model=name,training_cutoff=target-1,**item))
                    if progress: progress(f'{name}: fit through {target-1} ({len(training):,} rows)')
                scores = model.score_rows(current)
                ranking = rank_numbers(scores)
                cutoff,config = model.training_cutoff,model.configuration()
            # Outcome access occurs after this model's scores/ranking exist.
            actual = set(data.iloc[target-1][MAIN_COLUMNS].astype(int))
            record = dict(model=name,target_draw=target,feature_cutoff=target-1,training_cutoff=cutoff,
                          target_seed=target_seed,**rank_metrics(ranking,actual))
            if audit:
                record.update(actual=json.dumps(sorted(actual)),top6=json.dumps(ranking[:6]),
                              ranking=json.dumps(ranking),scores=json.dumps(scores,sort_keys=True),
                              configuration=json.dumps(config,sort_keys=True))
            if tickets:
                hits = [len(set(weighted_ticket(scores,seed=_seed(seed,target,1000+j))) & actual) for j in range(tickets)]
                record.update(weighted_tickets=tickets,weighted_mean_hits=float(np.mean(hits)),
                              weighted_hit_distribution=json.dumps(np.bincount(hits,minlength=7).tolist()))
            results.append(record)
        configurations[name] = model.configuration() if model is not None else dict(model='RandomModel',seed=seed,ties='uniform_random')
        runtimes[name] = round(perf_counter()-began,3)
        if progress: progress(f'{name}: {len(targets)} targets in {runtimes[name]:.2f}s')
    table = pd.DataFrame(results)
    table.attrs.update(model_configurations=configurations,model_runtime_seconds=runtimes)
    return table,pd.DataFrame(importances)


def summarize_rankings(results, *, simulations=2000, bootstraps=2000, seed=42, block_length=26):
    """Circular moving-block bootstrap over targets; paired baseline draws.

    Simulated random tickets use the exact Hypergeom(45,6,6) hit distribution.
    Their average distribution is a random-policy reference, not proof of a
    model's future advantage. Intervals are descriptive and uncorrected.
    """
    if min(simulations,bootstraps,block_length)<1:
        raise ValueError('Simulation, bootstrap and block counts must be positive')
    baseline = results[results.model=='RandomModel'].sort_values('target_draw')
    n = len(baseline)
    if not n or baseline.target_draw.duplicated().any(): raise ValueError('Missing or duplicate baseline targets')
    rng = np.random.default_rng(seed)
    null = rng.hypergeometric(6,39,6,size=(simulations,n)).mean(axis=1)
    length = min(block_length,n)
    starts = rng.integers(0,n,size=(bootstraps,math.ceil(n/length)))
    indices = ((starts[:,:,None]+np.arange(length)) % n).reshape(bootstraps,-1)[:,:n]
    comparison,blocks=[],[]
    for name,group in results.groupby('model',sort=False):
        group=group.sort_values('target_draw')
        if group.target_draw.tolist()!=baseline.target_draw.tolist():
            raise ValueError('Paired comparison requires identical target draws')
        hits=group.hits.to_numpy()
        delta=hits-baseline.hits.to_numpy()
        ci=np.quantile(delta[indices].mean(axis=1),[.025,.975])
        mean_ci=np.quantile(hits[indices].mean(axis=1),[.025,.975])
        row=dict(model=name,targets=n,avg_hits=float(hits.mean()),theoretical_hits=.8,
                 delta_vs_random=float(delta.mean()),paired_ci_low=float(ci[0]),paired_ci_high=float(ci[1]),
                 avg_ci_low=float(mean_ci[0]),avg_ci_high=float(mean_ci[1]),
                 mean_winning_rank=float(group.mean_winning_rank.mean()),best=int(hits.max()),
                 random_reference_tail=float((1+np.sum(null>=hits.mean()))/(simulations+1)))
        row.update({f'recall_{k}':float(group[f'recall_{k}'].mean()) for k in (6,10,15)})
        row.update({f'rate_{k}_plus':float((hits>=k).mean()) for k in (3,4,5)})
        row.update({f'hits_{k}':int((hits==k).sum()) for k in range(7)})
        comparison.append(row)
        for label,chunk in zip(('early','middle','recent'),np.array_split(np.arange(n),3)):
            if not len(chunk): continue
            blocks.append(dict(model=name,block=label,start_draw=int(group.iloc[chunk[0]].target_draw),
                               end_draw=int(group.iloc[chunk[-1]].target_draw),targets=len(chunk),
                               avg_hits=float(hits[chunk].mean()),delta_vs_random=float(delta[chunk].mean()),
                               mean_winning_rank=float(group.iloc[chunk].mean_winning_rank.mean())))
    comparison=pd.DataFrame(comparison)
    comparison['random_reference_bonferroni']=np.minimum(1,comparison.random_reference_tail*max(1,len(comparison)-1))
    return dict(comparison=comparison,time_blocks=pd.DataFrame(blocks),
                random_simulations=dict(simulations=simulations,seed=seed,theoretical_avg_hits=.8,
                                        empirical_avg_hits=float(null.mean()),
                                        interval_95=np.quantile(null,[.025,.975]).tolist(),
                                        expected_mean_winning_rank=23.,
                                        expected_recall={str(k):k/45 for k in (6,10,15)}),
                bootstrap=dict(replicates=bootstraps,block_length=length,method='circular moving block'),
                warnings=['Exploratory model comparisons; no tuning on these targets.',
                          'Overlapping feature windows and repeated model comparisons can create unstable differences.',
                          'Paired intervals are not multiplicity-corrected; compare time blocks and ablations.',
                          'Weighted ticket metrics are separate from deterministic ranking metrics.'])
