"""H24 descriptive tables/plots; encoding agreement is never independent evidence."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .symbolic import (ALPHAS,encode_all,transition_diagnostic,entropy_counts,bic,run_diagnostic)
from .symbolic_search import FAMILIES,metric_vector


def agreement_matrix(encodings):
    names=list(encodings);matrix=np.eye(len(names))
    for i,name in enumerate(names):
        a=encodings[name]['symbols'];A=encodings[name]['alphabet']
        for j in range(i):
            b=encodings[names[j]]['symbols'];B=encodings[names[j]]['alphabet']
            counts=np.bincount(a*B+b,minlength=A*B).reshape(A,B);p=counts/counts.sum()
            expected=p.sum(1)[:,None]*p.sum(0)[None,:];nz=p>0
            mi=np.sum(p[nz]*np.log2(p[nz]/expected[nz]))
            denominator=np.sqrt(entropy_counts(counts.sum(1))*entropy_counts(counts.sum(0)))
            matrix[i,j]=matrix[j,i]=float(mi/denominator) if denominator else 0.
    return names,matrix


def transition_stability(s,A,source,destination):
    intervals=[('early',0,len(s)//3),('middle',len(s)//3,2*len(s)//3),('recent',2*len(s)//3,len(s))]
    intervals += [('rolling',end-208,end) for end in sorted(set(range(208,len(s)+1,52))|{len(s)})]
    rows=[]
    for scope,lo,hi in intervals:
        r=transition_diagnostic(s[lo:hi],A)
        rows.append(dict(scope=scope,start=lo+201,end=hi+200,source=int(source),destination=int(destination),
            count=int(r['counts'][source,destination]),expected=float(r['expected'][source,destination]),
            residual=float(r['residual'][source,destination]),supported=bool(r['supported'][source,destination])))
    return rows


def diagnostics(x,directory):
    from src.random_matrix_cli import dump
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory=Path(directory);plots=directory/'plots';plots.mkdir(exist_ok=True)
    raw=metric_vector(x,details=True);inventory=raw['inventory'];dev=metric_vector(x[:900],details=True)
    names=list(inventory);boundaries={k:dict(alphabet=v['alphabet'],boundaries=v['boundaries'],fit=[1,200],symbols_start=201) for k,v in inventory.items()}
    dump(directory/'boundaries.json',boundaries)
    dump(directory/'alphabet_support.json',{k:v['support'] for k,v in inventory.items()})
    pd.DataFrame(dict(draw=np.arange(201,1246),**{k:v['symbols'] for k,v in inventory.items()})).to_csv(directory/'symbol_sequences.csv',index=False)
    support_rows=[];transition_rows=[];entropy_rows=[];loss_rows=[];word_rows=[];forbidden_rows=[]
    for name,r in inventory.items():
        A=r['alphabet'];support=r['support'];tr=r['transition']
        support_rows.extend(dict(encoding=name,symbol=i,count=c,probability=c/len(r['symbols']),rare=c<5) for i,c in enumerate(support['counts']))
        for i in range(A):
            for j in range(A):
                transition_rows.append(dict(encoding=name,source=i,destination=j,count=int(tr['counts'][i,j]),
                    expected=tr['expected'][i,j],residual=tr['residual'][i,j],supported=bool(tr['supported'][i,j]),
                    smoothed_probability=tr['probabilities'][i,j],row_entropy=tr['entropy'][i],row_concentration=tr['concentration'][i]))
        for k,H in enumerate(r['entropy']):entropy_rows.append(dict(encoding=name,order=k,conditional_entropy=H,reduction=r['entropy'][0]-H))
        for scope,actual in [('development',dev['inventory'][name]),('later',r)]:
            for k in range(4):
                for ai,alpha in enumerate(ALPHAS):
                    lower=min(actual['losses'][:k].ravel()) if k else actual['losses'][0,ai]
                    loss_rows.append(dict(scope=scope,encoding=name,order=k,alpha=alpha,logloss=actual['losses'][k,ai],
                        gain_order0=actual['losses'][0,ai]-actual['losses'][k,ai],gain_best_lower=lower-actual['losses'][k,ai],
                        training_BIC=bic(actual['symbols'][:actual['split']],A,k),dense_parameters=A**k*(A-1)))
        for L,w in r['words'].items():
            for i,word in enumerate(w['words']):
                word_rows.append(dict(encoding=name,length=L,word=','.join(map(str,word)),count=int(w['counts'][i]),
                    expected=w['expected'][i],lift=w['counts'][i]/w['expected'][i],deviance_residual=w['residual'][i],supported=bool(w['supported'][i])))
            forbidden_rows.append(dict(encoding=name,length=L,declared_words=A**L,eligible=w['eligible'],
                **{k:w[k] for k in ('missing_count','rare_count','missing_max_expected','missing_fraction','rare_max_expected')}))
    for filename,rows in [('alphabet_support.csv',support_rows),('transition_matrices.csv',transition_rows),('conditional_entropy.csv',entropy_rows),
        ('heldout_logloss.csv',loss_rows),('word_counts.csv',word_rows),('forbidden_summary.csv',forbidden_rows)]:pd.DataFrame(rows).to_csv(directory/filename,index=False)
    dump(directory/'run_summary.json',{name:r['runs'] for name,r in inventory.items()})
    real=json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))['full']
    winner=real['leaders']['transition'];encoding=winner['encoding'];i=winner['source'];j=winner['destination']
    stability=transition_stability(inventory[encoding]['symbols'],inventory[encoding]['alphabet'],i,j)
    pd.DataFrame(stability).to_csv(directory/'transition_stability.csv',index=False)
    word_winner=real['leaders']['word'];word_stability=[]
    if word_winner['word']:
        from .symbolic import word_diagnostic
        s=inventory[word_winner['encoding']]['symbols'];A=inventory[word_winner['encoding']]['alphabet'];L=word_winner['length']
        code=sum(v*A**(L-offset-1) for offset,v in enumerate(word_winner['word']))
        intervals=[('early',0,len(s)//3),('middle',len(s)//3,2*len(s)//3),('recent',2*len(s)//3,len(s))]
        intervals += [('rolling',end-208,end) for end in sorted(set(range(208,len(s)+1,52))|{len(s)})]
        for scope,lo,hi in intervals:
            w=word_diagnostic(s[lo:hi],A,L)
            word_stability.append(dict(scope=scope,start=lo+201,end=hi+200,encoding=word_winner['encoding'],word=word_winner['word'],
                count=int(w['counts'][code]),expected=float(w['expected'][code]),residual=float(w['residual'][code]),supported=bool(w['supported'][code])))
    dump(directory/'word_stability.json',word_stability)
    agreement_names,agreement=agreement_matrix(inventory)
    pd.DataFrame(agreement,index=agreement_names,columns=agreement_names).to_csv(directory/'representation_agreement.csv')
    # Audit exact-band sparsity without introducing a post-hoc alphabet.
    from .optimal_transport import draw_positions
    a=draw_positions(x)[200:];band_counts=np.array([((a>=lo)&(a<=lo+8)).sum(1) for lo in (1,10,19,28,37)]).T
    distinct,counts=np.unique(band_counts,axis=0,return_counts=True)
    dump(directory/'exact_band_support_audit.json',dict(observed_vectors=len(distinct),minimum_support=int(counts.min()),
        rare_vectors=int((counts<5).sum()),vectors=distinct,counts=counts,analysis_uses_fixed_reduced_alphabet10=True))
    def save(fig,name):
        fig.tight_layout();fig.savefig(plots/name,dpi=145);plt.close(fig)
    fig,axes=plt.subplots(4,2,figsize=(12,12))
    for ax,name in zip(axes.flat,names):
        r=inventory[name];ax.bar(np.arange(r['alphabet']),r['support']['counts']);ax.set(title=f"{name}: declared{r['alphabet']}, observed{r['support']['observed_symbols']}",xlabel='Symbol',ylabel='Count',xticks=range(r['alphabet']))
    save(fig,'01_symbol_frequency.png')
    fig,axes=plt.subplots(4,2,figsize=(12,15))
    for ax,name in zip(axes.flat,names):
        r=inventory[name];im=ax.imshow(r['transition']['probabilities'],vmin=0,vmax=1,cmap='viridis')
        ax.set(title=f'{name}: order1, alpha1',xlabel='Destination',ylabel='Source',xticks=range(r['alphabet']),yticks=range(r['alphabet']));fig.colorbar(im,ax=ax,fraction=.035)
    save(fig,'02_transition_matrices.png')
    fig,axes=plt.subplots(4,2,figsize=(12,12))
    for ax,name in zip(axes.flat,names):
        ax.plot(range(4),inventory[name]['entropy'],'o-');ax.set(title=name,xlabel='Order',ylabel='Plugin conditional entropy (bits)',xticks=range(4))
    save(fig,'03_conditional_entropy.png')
    fig,axes=plt.subplots(4,2,figsize=(12,12))
    for ax,name in zip(axes.flat,names):
        r=inventory[name]
        for ai,alpha in enumerate(ALPHAS):ax.plot(range(4),r['losses'][:,ai],'o-',label=f'alpha{alpha}')
        ax.set(title=f'{name}, later901..1245',xlabel='Max order (support backoff)',ylabel='Prequential logloss (nats)',xticks=range(4));ax.legend(fontsize=8)
    save(fig,'04_heldout_logloss.png')
    fig,ax=plt.subplots(figsize=(7,6));r=inventory[encoding]['transition'];masked=np.where(r['supported'],r['residual'],np.nan)
    extent=np.nanmax(abs(masked));im=ax.imshow(masked,cmap='coolwarm',vmin=-extent,vmax=extent)
    ax.plot(j,i,'ks',fillstyle='none',markersize=16);fig.colorbar(im,ax=ax,label='Pearson residual')
    ax.set(title=f'Strongest standardized transition: {encoding} {i}->{j}',xlabel='Destination',ylabel='Source');save(fig,'05_transition_residual.png')
    r=inventory[word_winner['encoding']]['words'][word_winner['length']]
    supported=np.flatnonzero(r['supported']);chosen=supported[np.argsort(abs(r['residual'][supported]))[-16:]]
    fig,ax=plt.subplots(figsize=(12,5));xpos=np.arange(len(chosen))
    ax.bar(xpos-.2,r['counts'][chosen],width=.4,label='Observed');ax.bar(xpos+.2,r['expected'][chosen],width=.4,label='Lower-order expectation')
    ax.set(xticks=xpos,xticklabels=['/'.join(map(str,w)) for w in r['words'][chosen]],ylabel='Word count',title=f"{word_winner['encoding']}, L{word_winner['length']}: supported word inspection")
    ax.tick_params(axis='x',rotation=65);ax.legend();save(fig,'06_word_anomaly.png')
    with np.load(directory/'null_metrics_full.npz') as f:null_raw=f['values']
    run_name=real['leaders']['run_lag']['encoding'];r=inventory[run_name]['runs'];index=raw['keys'].index(f'run_lag|{run_name}|longest')
    fig,axes=plt.subplots(1,2,figsize=(11,4));axes[0].hist(r['lengths'],bins=np.arange(1,r['longest']+2)-.5)
    axes[0].set(title=f'{run_name}: observed run lengths',xlabel='Length',ylabel='Count')
    axes[1].hist(null_raw[:199,index],alpha=.6,label='IID');axes[1].hist(null_raw[199:,index],alpha=.6,label='Fixed margins')
    axes[1].axvline(r['longest'],color='black',label='Real longest');axes[1].set(title='Descriptive longest-run comparison',xlabel='Longest run');axes[1].legend()
    save(fig,'07_run_length.png')
    maxima=pd.read_csv(directory/'null_maxima.csv')
    for number,kind in [(8,'iid'),(9,'fixed_margins')]:
        fig,axes=plt.subplots(2,3,figsize=(12,7));subset=maxima[(maxima.scope=='full')&(maxima.null_model==kind)]
        for ax,family in zip(axes.flat,FAMILIES):
            ax.hist(subset[family],bins=25);ax.axvline(real['maxima'][family],color='red',label='Real');ax.set(title=family,xlabel='Own complete-search maximum z');ax.legend(fontsize=8)
        fig.suptitle(f'Real vs{kind},199rebuilt histories');save(fig,f'{number:02d}_{kind}_global_max.png')
    frame=pd.DataFrame(stability);rolling=frame[frame.scope=='rolling']
    fig,axes=plt.subplots(1,2,figsize=(11,4));supported=rolling[rolling.supported]
    axes[0].plot(supported.end,supported.residual,'o-');axes[0].axhline(0,color='grey');axes[0].set(title=f'{encoding}:{i}->{j}, W208 supported only',xlabel='Endpoint',ylabel='Residual')
    era=frame[frame.scope!='rolling'];axes[1].bar(era.scope,era.residual);axes[1].set(title='Fixed transition across eras',ylabel='Residual (support flags in CSV)')
    save(fig,'10_transition_stability.png')
    fig,ax=plt.subplots(figsize=(8,7));im=ax.imshow(agreement,vmin=0,vmax=1,cmap='viridis');fig.colorbar(im,ax=ax,label='Normalized mutual information')
    ax.set(xticks=range(8),yticks=range(8),xticklabels=names,yticklabels=names,title='Descriptive representation agreement');ax.tick_params(axis='x',rotation=45)
    save(fig,'11_representation_agreement.png')
    dump(directory/'diagnostics_summary.json',dict(encodings=names,plots=11,transition_winner=winner,word_winner=word_winner,
        agreement_descriptive_only=True,analysis_symbols=[201,1245],bin_fit=[1,200]))
    print('H24 diagnostics:11plots and symbolic tables saved',flush=True)
