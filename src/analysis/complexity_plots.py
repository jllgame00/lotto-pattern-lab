"""H14 inspection figures; raw proxies and plots are not randomness proofs."""
import json
import numpy as np
import pandas as pd
from src.analysis.complexity_search import FAMILIES
from src.complexity_cli import load_calibration
from src.recurrence_cli import dump


def plots(x,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=directory/'plots';out.mkdir(exist_ok=True)
    real=json.loads((directory/'real_summary.json').read_text())['full'];table=pd.read_csv(directory/'full_metrics.csv')
    null=pd.read_csv(directory/'null_maxima.csv');null=null[null.scope=='full'].reset_index(drop=True)
    cache=np.load(directory/'null_metrics_full.npz')['values'];c=load_calibration(directory,1245)
    comparisons=pd.read_csv(directory/'global_null_comparison.csv');comparisons=comparisons[comparisons.scope=='full']
    keys={key:i for i,key in enumerate(c['keys'])}
    def save(name):plt.tight_layout();plt.savefig(out/name,dpi=150);plt.close()
    sh=table[(table.scope=='whole')&(table.kind=='block_entropy')&(table.L==1)&table.representation.str.fullmatch('number[0-9]{2}')]
    plt.figure(figsize=(12,4));plt.bar(np.arange(1,46),sh.measurement)
    p=6/45;plt.axhline(-p*np.log2(p)-(1-p)*np.log2(1-p),color='red',linestyle='--',label='IID Bernoulli H(6/45)')
    plt.xlabel('Number');plt.ylabel('Shannon entropy bits');plt.legend();save('per_number_shannon.png')
    def family_hist(family,name):
        plt.figure(figsize=(9,4))
        for kind,g in null.groupby('null_model'):plt.hist(g[family],bins=22,alpha=.45,label=kind)
        plt.axvline(real['maxima'][family],color='red',label='Real global maximum');plt.legend();plt.xlabel('Calibrated own-search maximum');save(name)
    family_hist('entropy','real_vs_surrogate_entropy.png')
    representatives=['number09','full_binary','draw_packed','sorted_numbers','adjacent_gaps']
    fig,axes=plt.subplots(1,5,figsize=(17,4))
    for name,ax in zip(representatives,axes):
        row=table[(table.scope=='whole')&(table.representation==name)&(table.kind=='lz78')].iloc[0];index=keys[row.key]
        groups=[-cache[null.null_model==kind,index] for kind in ('iid','fixed_margins','draw_shuffle')]
        ax.boxplot(groups,tick_labels=['IID','fixed','shuffle']);ax.axhline(row.measurement,color='red');ax.set_title(name,fontsize=9);ax.set_ylabel('LZ78 normalized')
    save('lz_complexity_comparison.png')
    selected=['number09','full_binary','draw_packed','sorted_numbers','adjacent_gaps'];summary=[]
    fig,axes=plt.subplots(1,3,figsize=(17,5))
    for compressor,ax in zip(('zlib','bz2','lzma'),axes):
        base=table[(table.scope=='whole')&(table.kind=='compression')&(table.compressor==compressor)]
        chosen=base.set_index('representation').loc[selected]
        for j,(label,kind) in enumerate([('Real',None),('IID','iid'),('fixed','fixed_margins'),('shuffle','draw_shuffle')]):
            values=[]
            for name,row in chosen.iterrows():
                index=keys[row.key];ratio=float(row.measurement) if kind is None else float(-cache[null.null_model==kind,index].mean())
                values.append(ratio);summary.append(dict(representation=name,compressor=compressor,history=label,ratio=ratio,
                    raw_bytes=int(row.raw_bytes),compressed_bytes=float(row.compressed_bytes) if kind is None else ratio*row.raw_bytes))
            ax.bar(np.arange(5)+(j-1.5)*.2,values,width=.2,label=label)
        ax.set_xticks(np.arange(5),selected,rotation=40,ha='right',fontsize=8);ax.set_title(compressor);ax.set_ylabel('Compressed/raw including headers');ax.legend(fontsize=7)
    save('compression_ratio_comparison.png');pd.DataFrame(summary).to_csv(directory/'compression_comparison.csv',index=False)
    family_hist('chronological','chronological_vs_shuffled.png')
    rolling=table[table.scope=='rolling'];fig,axes=plt.subplots(5,1,figsize=(12,12))
    for family,ax in zip(FAMILIES[:5],axes):
        leader=real['leaders'][family];rep=leader['representation'];kind=leader['kind']
        chosen=rolling[(rolling.family==family)&(rolling.representation==rep)&(rolling.kind==kind)]
        if chosen.empty:chosen=rolling[(rolling.family==family)&(rolling.representation=='draw_packed')]
        for W,g in chosen.groupby('window'):ax.plot(g.endpoint,g.z,marker='.',label=f'W{int(W)}')
        ax.set_ylabel(family+' z');ax.set_title(str(chosen.representation.iloc[0]) if len(chosen) else family,fontsize=9);ax.legend(fontsize=7)
    axes[-1].set_xlabel('Window endpoint; equally searched under each null');save('rolling_complexity.png')
    strongest=rolling[rolling.eligible].sort_values('z',ascending=False,kind='stable').iloc[0]
    fig,axes=plt.subplots(2,1,figsize=(12,6));W=int(strongest.window);end=int(strongest.endpoint);start=end-W+1
    if strongest.representation.startswith('number'):
        n=int(strongest.representation[6:]);values=x[:,n-1].astype(int);axes[0].step(np.arange(1,len(x)+1),values,where='mid');axes[0].axvspan(start,end,alpha=.25,color='orange')
    axes[0].set_title(f'Selected local region {start}..{end}: {strongest.representation}; z={strongest.z:.3f} (global correction required)')
    chosen=rolling[(rolling.representation==strongest.representation)&(rolling.kind==strongest.kind)&(rolling.window==W)]
    axes[1].plot(chosen.endpoint,chosen.measurement,marker='o');axes[1].axvspan(start,end,alpha=.2,color='orange');axes[1].set_xlabel('Endpoint');axes[1].set_ylabel('Raw selected metric')
    save('strongest_low_complexity_region.png');dump(directory/'strongest_rolling_region.json',dict(strongest.dropna().to_dict(),start=start,end=end))
    fig,axes=plt.subplots(2,3,figsize=(15,7))
    for family,ax in zip(FAMILIES,axes.ravel()):
        for kind,g in null.groupby('null_model'):ax.hist(g[family],bins=18,alpha=.4,label=kind)
        ax.axvline(real['maxima'][family],color='red');ax.set_title(family);ax.set_xlabel('Own-search maximum')
    axes[0,0].legend(fontsize=7);save('global_max_statistics.png')
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    pe=table[(table.scope=='whole')&(table.representation=='sum')&(table.kind=='permutation_entropy')].pivot(index='m',columns='tau',values='measurement')
    se=table[(table.scope=='whole')&(table.representation=='sum')&(table.kind=='sample_entropy')].pivot(index='m',columns='r',values='measurement')
    for ax,matrix,title in zip(axes,[pe,se],['Sum normalized Permutation Entropy','Sum Sample Entropy (nats)']):
        im=ax.imshow(matrix,aspect='auto');ax.set_xticks(range(len(matrix.columns)),matrix.columns);ax.set_yticks(range(len(matrix.index)),matrix.index)
        ax.set_title(title);ax.set_ylabel('m');plt.colorbar(im,ax=ax)
    axes[0].set_xlabel('Delay');axes[1].set_xlabel('r/std');save('permutation_sample_entropy.png')
    regimes=pd.read_csv(directory/'regimes.csv');fig,axes=plt.subplots(2,1,figsize=(12,7))
    axes[0].plot(regimes.endpoint,regimes.metric,label='Oriented metric');axes[0].plot(regimes.endpoint,regimes.q_low,label='Past1/3 quantile');axes[0].plot(regimes.endpoint,regimes.q_high,label='Past2/3 quantile')
    axes[0].axvline(900,color='black',linestyle='--');axes[0].legend(fontsize=8);axes[0].set_title('Development-frozen metric; causal thresholds; descriptive states')
    means=regimes[regimes.state!='UNKNOWN'].groupby('state')[['overlap','own_expected_overlap']].mean()
    means.plot.bar(ax=axes[1]);axes[1].set_ylabel('Next overlap / own-frequency expectation');axes[1].set_xlabel('Descriptive state; not a predictive evaluation')
    save('descriptive_regimes.png')
