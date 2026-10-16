"""Descriptive HMM stability/null diagnostics, separate from predictive scoring."""
import numpy as np
import pandas as pd
from src.models.bayesian import observation_matrix
from src.models.bernoulli_hmm import BernoulliHMM
from src.research_seal import assert_open


def hmm_fit_records(name,model):
    h=model.hmm; records=[]
    for j in range(45):
        ll=[item['log_likelihood'][j] for item in h.initializations]
        spreads=[np.ptp(item['emissions'][j]) for item in h.initializations]
        for state in range(h.states):
            records.append(dict(model=name,training_cutoff=model.training_cutoff,number=j+1,state=state,
                emission=h.emissions[j,state],self_transition=h.transitions[j,state,state],
                state_probability=h.state[j,state],next_score=h.next_score()[j],
                iterations=h.iterations[j],converged=bool(h.converged[j]),log_likelihood=h.log_likelihood[j],
                initialization_loglike_range=np.ptp(ll),initialization_spread_range=np.ptp(spreads),
                **{f'transition_{k}':h.transitions[j,state,k] for k in range(h.states)}))
    return records


def state_relationships(states,features):
    assert_open(features,'target_draw')
    columns=['rate_52','current_gap','periodicity_score','strong_regime']
    frame=states.merge(features[['target_draw','number',*columns]],on=['target_draw','number'],validate='many_to_one')
    records=[]
    for (model,number),group in frame.groupby(['model','number']):
        for probability in ('cold_probability','hot_probability'):
            for feature in columns:
                pair=group[[probability,feature]].dropna()
                correlation=pair[probability].corr(pair[feature],method='spearman') if pair.nunique().min()>1 else np.nan
                records.append(dict(model=model,number=number,probability=probability,feature=feature,
                    observations=len(pair),spearman=correlation,
                    status='exploratory association; no corrected significance test'))
    return pd.DataFrame(records)


def parameter_stability(fits):
    records=[]
    for (model,number,state),group in fits.groupby(['model','number','state']):
        group=group.sort_values('training_cutoff')
        records.append(dict(model=model,number=number,state=state,fits=len(group),
            emission_mean=group.emission.mean(),emission_std=group.emission.std(),
            mean_abs_emission_change=group.emission.diff().abs().mean(),
            self_transition_mean=group.self_transition.mean(),self_transition_std=group.self_transition.std(),
            convergence_fraction=group.converged.mean(),initialization_loglike_range=group.initialization_loglike_range.mean(),
            initialization_spread_range=group.initialization_spread_range.mean()))
    return pd.DataFrame(records)


def null_diagnostics(features,*,numbers=(7,17,34),repeats=39,seed=42,max_iter=40):
    assert_open(features,'target_draw')
    x=observation_matrix(features)[-260:]; rng=np.random.default_rng(seed)
    sequences=[]; keys=[]
    for number in numbers:
        original=x[:,number-1]
        for repeat in range(repeats+1):
            sequences.append(original if repeat==0 else rng.permutation(original)); keys.append((number,repeat))
    matrix=np.array(sequences).T; rows=[]; summaries=[]
    for states in (2,3):
        hmm=BernoulliHMM(states=states,seed=seed,max_iter=max_iter).fit(matrix)
        p=np.clip(matrix.mean(0),1e-9,1-1e-9)
        iid=(matrix*np.log(p)+(1-matrix)*np.log1p(-p)).sum(0)
        for j,(number,repeat) in enumerate(keys):
            rows.append(dict(states=states,number=number,repeat=repeat,observed=repeat==0,
                emission_spread=np.ptp(hmm.emissions[j]),persistence=np.diag(hmm.transitions[j]).mean(),
                loglike_gain=hmm.log_likelihood[j]-iid[j],converged=hmm.converged[j],iterations=hmm.iterations[j]))
    table=pd.DataFrame(rows)
    for (states,number),group in table.groupby(['states','number']):
        real=group[group.observed].iloc[0]; null=group[~group.observed]
        for metric in ('emission_spread','persistence','loglike_gain'):
            p=(1+(null[metric]>=real[metric]).sum())/(repeats+1)
            summaries.append(dict(states=states,number=number,metric=metric,observed=real[metric],
                null_mean=null[metric].mean(),permutation_p=p,permutations=repeats,
                p_bonferroni=min(1,p*len(numbers)*2*3)))
    return table,pd.DataFrame(summaries)


def plot_states(states,features,output,numbers=(7,17,34)):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output.mkdir(parents=True,exist_ok=True)
    for number in numbers:
        fig,axes=plt.subplots(4,1,figsize=(12,9),sharex=True)
        for name,group in states[states.number==number].groupby('model'):
            axes[0].plot(group.target_draw-1,group.hot_probability,label=f'{name} hot')
            axes[1].plot(group.target_draw-1,group.cold_probability,label=f'{name} cold')
        selected=features[(features.number==number)&features.target_draw.isin(states.target_draw)]
        axes[2].plot(selected.feature_cutoff,selected.rate_52,label='52-draw frequency')
        axes[3].plot(selected.feature_cutoff,selected.periodicity_score,label='104-draw periodicity score')
        axes[3].fill_between(selected.feature_cutoff,0,selected.strong_regime*.6,alpha=.2,label='Causal heuristic strong regime')
        for ax in axes: ax.legend(loc='upper left'); ax.grid(alpha=.2)
        axes[-1].set_xlabel('Observed draw cutoff; probabilities filtered with past-fitted parameters')
        fig.suptitle(f'Number {number}: exploratory causal states; no validated latent regime')
        fig.tight_layout(); fig.savefig(output/f'number_{number:02d}_regimes.png',dpi=140); plt.close(fig)
