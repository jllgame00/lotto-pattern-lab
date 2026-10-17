"""Descriptive Phase12 figures; plot selection is not an inferential test."""
import json
import numpy as np
import pandas as pd
from src.analysis.multiscale import representations,ENDPOINTS
from src.analysis.wavelet import morlet_transform
from src.analysis.ssa import decompose
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.recurrence_cli import dump


def plots(x,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=directory/'plots';out.mkdir(exist_ok=True)
    real=json.loads((directory/'real_maxima.json').read_text());names,y=representations(x,cutoff=len(x))
    regions=pd.read_csv(directory/'localized_regions.csv');ssa=json.loads((directory/'ssa_search.json').read_text())
    chosen=real['leaders']['wavelet_region']['region']
    has_region=chosen is not None
    if not has_region:
        peak=real['leaders']['wavelet_peak'];i=names.index(peak['series'])
        chosen=dict(series=i,start=peak['peak_draw'],end=peak['peak_draw'],
            period=peak['peak_period'],score=0.,duration=0)
    i=int(chosen['series'])
    histories={'real':x,'iid':iid_surrogate(len(x),seed=120043),
        'fixed_margin':constrained_surrogate(x,seed=120044)}
    transforms={k:morlet_transform(representations(h,cutoff=len(h))[1]) for k,h in histories.items()}
    def save(name):
        plt.tight_layout();plt.savefig(out/name,dpi=150);plt.close()
    # Same real-selected series, scales, time extent and color limits in all three.
    vmax=max(float(t['power'][i].max()) for t in transforms.values())
    for label,t in transforms.items():
        plt.figure(figsize=(11,4));p=np.where(t['valid'],t['power'][i],np.nan)
        plt.pcolormesh(np.arange(1,len(x)+1),t['periods'],p,shading='nearest',vmin=0,vmax=vmax,cmap='magma')
        plt.yscale('log');plt.colorbar(label='Standardized wavelet power');plt.xlabel('Historical draw');plt.ylabel('Period')
        plt.title(f"{label}: {names[i]}, COI masked (descriptive)");save(f'{label}_scalogram.png')
    t=transforms['real'];plt.figure(figsize=(10,4))
    plt.pcolormesh(np.arange(1,len(x)+1),t['periods'],np.where(t['valid'],t['power'][i],np.nan),shading='nearest',cmap='magma')
    plt.axvline(chosen['start'],color='cyan');plt.axvline(chosen['end'],color='cyan')
    plt.axhline(chosen['period'],color='cyan',linestyle=':');plt.xlim(max(1,chosen['start']-100),min(len(x),chosen['end']+100))
    plt.yscale('log');plt.xlabel('Draw');plt.ylabel('Period')
    plt.title(f"Strongest real region: {names[i]}; score={chosen['score']:.2f}" if has_region else 'No eligible localized region; peak shown descriptively')
    save('strongest_localized_region.png')
    plt.figure(figsize=(8,4))
    for label,t in transforms.items():plt.plot(t['periods'],t['global_power'][i],'o-',label=label)
    plt.xlabel('Period');plt.ylabel('Mean power within COI');plt.legend();save('global_power_comparison.png')
    leader=real['leaders']['ssa_pair'];j=names.index(leader['series']);L=leader['L'];end=leader['end']
    result=decompose(y[end-416:end,j],L,components=8)
    pair=max(leader['pairs'],key=lambda p:p['score']) if leader['pairs'] else dict(first=0,second=1)
    plt.figure(figsize=(8,4));plt.plot(np.arange(1,L+1),result['energy_ratios'],'o-',markersize=3)
    plt.xlabel('SSA component');plt.ylabel('Trajectory energy share');plt.title(f"{leader['series']}; L={L}; draws{end-415}..{end}")
    save('ssa_singular_spectrum.png')
    index=np.arange(end-415,end+1);selected=[pair['first'],pair['second']]
    plt.figure(figsize=(11,4));plt.plot(index,y[end-416:end,j]-result['mean'],alpha=.3,label='Centered observed')
    plt.plot(index,result['components'][selected].sum(0),label='Candidate pair reconstruction' if leader['pairs'] else 'Leading2; no eligible pair')
    plt.plot(index,result['components'][0],alpha=.6,label='Leading component');plt.legend();plt.xlabel('Draw');plt.ylabel('Original series units')
    save('ssa_reconstruction.png')
    # Waveform agreement supplements the primary period/amplitude stability score.
    # It is descriptive and is not substituted into the completed null test.
    stability=real['leaders']['ssa_stability'];j=names.index(stability['series']);L=stability['L']
    agreements_reconstruction=[];previous=None
    fig,ax=plt.subplots(figsize=(11,4))
    for end in ENDPOINTS:
        row=next(r for r in ssa if r['series']==stability['series'] and r['L']==L and r['end']==end)
        result=decompose(y[end-416:end,j],L,components=8)
        if not row['pairs']:previous=None;continue
        pair=max(row['pairs'],key=lambda p:p['score'])
        reconstruction=result['components'][[pair['first'],pair['second']]].sum(0)
        ax.plot(np.arange(end-415,end+1),reconstruction,label=f'{end-415}..{end}, P={pair["period"]:.2f}')
        if previous:
            old_end,old_pair,old=previous;overlap=416-(end-old_end)
            if overlap>1:
                a=old[-overlap:];b=reconstruction[:overlap]
                corr=float(np.corrcoef(a,b)[0,1]) if np.std(a)>0 and np.std(b)>0 else 0.
                agreements_reconstruction.append(dict(series=stability['series'],L=L,previous_end=old_end,end=end,
                    previous_period=old_pair['period'],period=pair['period'],overlap=overlap,correlation=corr))
        previous=(end,pair,reconstruction)
    ax.set_xlabel('Historical draw');ax.set_ylabel('Reconstructed centered activity')
    ax.set_title('Primary stability leader across fixed windows (descriptive waveform comparison)');ax.legend()
    save('ssa_stability_reconstruction.png')
    pd.DataFrame(agreements_reconstruction).to_csv(directory/'ssa_reconstruction_stability.csv',index=False)
    null=pd.read_csv(directory/'null_maxima.csv');fig,axes=plt.subplots(2,3,figsize=(13,7))
    for ax,family in zip(axes.flat,real['maxima']):
        for label,g in null.groupby('null_model'):ax.hist(g[family],alpha=.55,label=label,bins=18)
        ax.axvline(real['maxima'][family],color='red');ax.set_title(family)
    axes[0,0].legend();save('real_vs_null_statistics.png')
    rolling=[]
    for label,t in transforms.items():
        for endpoint in range(312,1246,26):
            p=np.where(t['valid'][:,endpoint-208:endpoint],t['power'][:,:,endpoint-208:endpoint],0)
            rolling.append(dict(history=label,end=endpoint,wavelet_peak=float(p.max())))
    rolling=pd.DataFrame(rolling);rolling.to_csv(directory/'rolling_wavelet_strength.csv',index=False)
    fig,axes=plt.subplots(2,1,figsize=(11,6))
    for label,g in rolling.groupby('history'):axes[0].plot(g.end,g.wavelet_peak,label=label)
    axes[0].legend();axes[0].set_ylabel('Rolling max CWT power')
    sf=pd.DataFrame(ssa)
    for L,g in sf.groupby('L'):axes[1].plot(g.groupby('end').ssa_pair.max(),label=f'L{L}')
    axes[1].legend();axes[1].set_xlabel('Window endpoint');axes[1].set_ylabel('Real max SSA pair score')
    save('rolling_multiscale_strength.png')
    rows=pd.read_csv(directory/'walk_forward_26/predictions.csv')
    activity=[];freq=rows[rows.model=='Frequency26'].set_index('target_draw')
    for row in rows[rows.model.isin(['WaveletPhaseModel','SSAModel'])].itertuples():
        own=json.loads(row.scores);reference=json.loads(freq.loc[row.target_draw,'scores'])
        changed=sum(abs(own[str(n)]-reference[str(n)])>1e-12 for n in range(1,46))
        activity.append(dict(model=row.model,target_draw=row.target_draw,nonfallback_numbers=changed,
            ranking_equals_frequency=row.ranking==freq.loc[row.target_draw,'ranking']))
    pd.DataFrame(activity).to_csv(directory/'model_activity.csv',index=False)
    fig,axes=plt.subplots(2,1,figsize=(12,6))
    for ax,name in zip(axes,['WaveletPhaseModel','SSAModel']):
        row=rows[(rows.model==name)&(rows.target_draw==1245)].iloc[0]
        ranking=json.loads(row.ranking);scores=json.loads(row.scores)
        ax.bar(np.arange(45),[scores[str(n)] for n in ranking]);ax.set_xticks(np.arange(45),ranking,fontsize=7)
        ax.set_title(f'{name}, historical target1245; training history <=1244');ax.set_ylabel('Score')
    save('predictive_ranking_example.png')
    # Descriptive overlap requires matching number/shape, period and overlapping time.
    agreements=[]
    for region in regions.to_dict('records'):
        name=names[int(region['series'])]
        for row in ssa:
            if row['series']!=name:continue
            overlap=max(0,min(region['end'],row['end'])-max(region['start'],row['start'])+1)
            if not overlap:continue
            for pair in row['pairs']:
                ratio=min(region['period'],pair['period'])/max(region['period'],pair['period'])
                if ratio>=.8:agreements.append(dict(series=name,wavelet_start=region['start'],wavelet_end=region['end'],
                    wavelet_period=region['period'],ssa_start=row['start'],ssa_end=row['end'],L=row['L'],
                    ssa_period=pair['period'],overlap=overlap,period_ratio=ratio))
    pd.DataFrame(agreements).to_csv(directory/'cross_method_overlap.csv',index=False)
    dump(directory/'descriptive_diagnostics.json',dict(strongest_wavelet_region=chosen if has_region else None,strongest_ssa_pair=leader,
        overlap_matches=len(agreements),independent_confirmation=False,
        repeated_scale_regions=[dict(series=n,period=float(p),count=int(c))
            for (n,p),c in regions.groupby(['name','period']).size().items() if c>1]))
