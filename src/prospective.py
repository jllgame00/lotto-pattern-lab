"""Offline, append-only prospective snapshots. Never used for retrospective selection.

The fixed local canonical boundary is1245. No network and no read of a following
row. This capability does not assert that a target was genuinely unseen; the
operator must establish that externally before treating a snapshot as prospective.
"""
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import importlib.metadata
import json
from pathlib import Path
import subprocess
from uuid import uuid4

import numpy as np
import pandas as pd
from src.collect.dataset import validate_history, MAIN_COLUMNS
from src.models.bernoulli_hmm import BernoulliHMM
from src.models.predictive import rank_numbers
from src.backtest.portfolios import make_portfolio

CANONICAL_CUTOFF=1245


def load_prospective_source(path):
    lines=[]
    with Path(path).open('rb') as stream:
        for _ in range(CANONICAL_CUTOFF+1):
            line=stream.readline()
            if not line: break
            if not line.strip(): raise ValueError('Single-line canonical rows required')
            lines.append(line)
    raw=b''.join(lines)
    frame=pd.read_csv(BytesIO(raw))
    if frame.draw_no.tolist()!=list(range(1,len(frame)+1)) or len(frame)>CANONICAL_CUTOFF:
        raise ValueError('Prospective source must be contiguous and within fixed canonical boundary')
    return validate_history(frame),sha256(raw).hexdigest()


def freeze_snapshot(source,output,*,seed=42):
    if seed<0: raise ValueError('Nonnegative seed required')
    data,digest=load_prospective_source(source)
    if len(data)<104: raise ValueError('At least104 observations required')
    x=np.array([np.isin(np.arange(1,46),row) for row in data[MAIN_COLUMNS].to_numpy()],dtype=float)
    configurations={}; values={}
    for name,half_life in [('BayesianStatic',None),('BayesianRecent',52)]:
        w=np.ones(len(x)) if half_life is None else 2**(-np.arange(len(x)-1,-1,-1)/half_life)
        values[name]=(2+w@x)/(15+w.sum())
        configurations[name]=dict(version=1,alpha=2,beta=13,half_life=half_life,history_start=1)
    for states in (2,3):
        name=f'HMM{states}'
        hmm=BernoulliHMM(states=states,seed=seed).fit(x[-260:])
        values[name]=hmm.next_score()
        configurations[name]=dict(version=1,states=states,window=260,max_iter=40,n_init=2,
            min_history=104,tolerance=1e-5,initial_state='uniform',history_start=max(1,len(x)-259),
            state_labels=['cold','hot'] if states==2 else ['cold','neutral','hot'],
            transition_pseudocounts='8 diagonal,1 off diagonal',emission_pseudocounts=[2,13],
            transitions=hmm.transitions.tolist(),emissions=hmm.emissions.tolist(),
            filtered_state=hmm.state.tolist(),converged=hmm.converged.tolist())
    values['Frequency52']=x[-52:].mean(0)
    configurations['Frequency52']=dict(version=1,window=52)
    models={}
    for name,scores in values.items():
        scores=dict(zip(range(1,46),scores.tolist())); ranking=rank_numbers(scores)
        models[name]=dict(configuration=configurations[name],scores=scores,
            rankings={str(k):ranking[:k] for k in (6,10,12,15)},
            portfolios={method:make_portfolio(scores,ranking[:12],budget=20,method=method,seed=seed)
                        for method in ('weighted','coverage')},seed=seed,pool_size=12,budgets=[1,5,10,20])
    root=Path(__file__).resolve().parent.parent
    def git(*args):
        try: return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.DEVNULL,timeout=5).strip()
        except (OSError,subprocess.SubprocessError): return None
    now=datetime.now(timezone.utc)
    git_status=git('status','--porcelain')
    payload=dict(schema_version=1,created_at=now.isoformat(),canonical_dataset_sha256=digest,
        hash_scope='Exact bytes of header and locally included rows, bounded at1245; no suffix read',
        latest_included_draw=int(data.draw_no.iloc[-1]),latest_included_date=str(data.draw_date.iloc[-1].date()),
        target_draw=int(data.draw_no.iloc[-1])+1,target_result_retrieved=False,
        prospective_status='unverified: caller must establish target was unseen at freeze time',
        git_commit=git('rev-parse','HEAD'),git_dirty=None if git_status is None else bool(git_status),seed=seed,models=models,
        library_versions={name:importlib.metadata.version(name) for name in ('numpy','scipy','pandas')},
        implementation_hashes={str(path.relative_to(root)):sha256(path.read_bytes()).hexdigest()
            for path in sorted((root/'src').rglob('*.py'))},
        caveats=['Experimental, no demonstrated advantage.',
                 'This command does not select models or weights from later results.',
                 'Draw1245 was previously accessed and is not a pristine holdout.',
                 'Portfolio budgets use prefixes of20 unique tickets. No target results included.'])
    directory=Path(output); directory.mkdir(parents=True,exist_ok=True)
    path=directory/f'draw_{payload["target_draw"]}_{now.strftime("%Y%m%dT%H%M%S%fZ")}_{uuid4().hex[:8]}.json'
    with path.open('x',encoding='utf-8') as stream: json.dump(payload,stream,indent=2,allow_nan=False)
    return path
