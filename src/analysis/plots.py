"""Nine-panel matplotlib artifact for any chosen Lotto number."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from .series import binary_series
from .periodicity import PeriodicityConfig


def plot_number(history,number,analysis,output_dir,config=None):
    config=config or PeriodicityConfig()
    series=binary_series(history)[number]
    tables=analysis['tables']
    yearly=tables['yearly_number_stats'].query('number == @number')
    monthly=tables['monthly_number_stats'].query('number == @number')
    rolling=tables['rolling_number_stats'].query('number == @number')
    regimes=tables['periodicity_regimes'].query('number == @number')
    acf=analysis['diagnostics'][number]['autocorrelation']
    spectrum=analysis['diagnostics'][number]['spectrum']
    appearances=series.index[series==1].to_numpy()
    fig,axes=plt.subplots(3,3,figsize=(19,13),layout='constrained')
    axs=axes.ravel()
    colors={26:'#1e88a8',52:'#df8030',104:'#7861ad'}
    fig.suptitle(f'Lotto {number:02d} | Temporal pattern exploration | draws 1-{len(series)}',fontsize=19,fontweight='bold')
    axs[0].vlines(appearances,0,1,color='#245e78',linewidth=.7)
    axs[0].set(title='1. Binary main-number appearances',xlabel='Draw',ylabel='Appearance',yticks=[0,1],ylim=(-.05,1.1))
    axs[1].plot(appearances[1:],np.diff(appearances),color='#245e78',linewidth=.8,marker='.',markersize=3)
    axs[1].set(title='2. Completed appearance gaps',xlabel='Later appearance draw',ylabel='Interval (draws)')
    axs[2].bar(yearly.year,yearly.appearance_rate,color='#245e78',width=.8)
    axs[2].axhline(6/45,color='#bd563d',linestyle='--',label='Uniform 6/45')
    axs[2].set(title='3. Yearly rate (partial years included)',xlabel='Year',ylabel='Appearances / eligible draws')
    axs[2].legend(fontsize=8)
    axs[3].bar(monthly.month,monthly.appearance_rate,color='#245e78')
    axs[3].axhline(6/45,color='#bd563d',linestyle='--',label='Uniform 6/45')
    axs[3].axhline(series.mean(),color='#4b8254',linestyle=':',label='Number overall rate')
    axs[3].set(title='4. Month-of-year normalized rate',xlabel='Calendar month',ylabel='Appearances / eligible draws',xticks=range(1,13))
    axs[3].legend(fontsize=8)
    for window,group in rolling.groupby('window_size'):
        color=colors.get(window,None)
        axs[4].plot(group.end_draw,group.appearance_rate,label=f'{window} draws',color=color,linewidth=.85)
        axs[5].plot(group.end_draw,group.periodicity_score,label=f'{window} draws',color=color,linewidth=.85)
    axs[4].axhline(6/45,color='gray',linestyle='--',linewidth=.8)
    axs[4].set(title='5. Trailing appearance rates',xlabel='Window endpoint draw',ylabel='Appearance rate')
    axs[5].set(title='6. Trailing periodicity score (not probability)',xlabel='Window endpoint draw',ylabel='Heuristic score',ylim=(0,1))
    for ax in (axs[4],axs[5]):
        if ax.get_legend_handles_labels()[1]: ax.legend(fontsize=8)
    if acf['status']=='ok':
        axs[6].bar(acf['lags'],[v if v is not None else np.nan for v in acf['correlations']],color='#245e78',width=.8)
        axs[6].axhline(0,color='gray',linewidth=.7)
    else:
        axs[6].text(.5,.5,acf['status'].replace('_',' '),ha='center',transform=axs[6].transAxes)
    axs[6].set(title='7. Full-history guarded autocorrelation',xlabel='Lag (draws); lag 0 excluded',ylabel='Biased ACF')
    if spectrum['status']=='ok':
        order=np.argsort(spectrum['periods'])
        axs[7].plot(np.array(spectrum['periods'])[order],np.array(spectrum['powers'])[order],color='#245e78',linewidth=.9)
        axs[7].set_xscale('log')
    else:
        axs[7].text(.5,.5,spectrum['status'].replace('_',' '),ha='center',transform=axs[7].transAxes)
    axs[7].set(title=f'8. Full-history spectrum (>= {config.min_cycles} cycles)',xlabel='Candidate period (draws, log scale)',ylabel='Hann spectral power')
    windows=analysis['metadata']['windows']
    for index,window in enumerate(windows):
        group=regimes[regimes.window_size==window]
        for r in group.itertuples():
            axs[8].broken_barh([(r.start_draw,r.end_draw-r.start_draw+1)],(index-.25,.5),facecolors=colors.get(window,'#245e78'))
            axs[8].plot(r.peak_draw,index,'k.',markersize=3)
    axs[8].set(title='9. High-score regimes (window endpoints)',xlabel='Draw; dots mark peaks',ylabel='Window size',
               yticks=range(len(windows)),yticklabels=windows,xlim=(1,len(series)),ylim=(-.5,len(windows)-.5))
    if regimes.empty: axs[8].text(.5,.5,'No qualifying regimes',ha='center',transform=axs[8].transAxes)
    for ax in axs:
        ax.grid(axis='y',alpha=.18)
        ax.spines[['top','right']].set_visible(False)
        ax.tick_params(labelsize=8)
        ax.title.set_fontsize(11)
    fig.supxlabel('EXPLORATORY: overlapping windows and multiple searches can create apparent patterns. Peaks and regimes do not establish prediction.',fontsize=10)
    output_dir=Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    path=output_dir/f'number_{number:02d}_temporal.png'
    fig.savefig(path,dpi=160,facecolor='white')
    plt.close(fig)
    return path
