"""H21 descriptive plots/tables and read-only frozen Graph comparison."""
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from .recurrence import research_matrix
from .random_matrix import RANKS,mp_reference,subspace_comparison,degenerate_groups
from .random_matrix_search import metric_vector

ROOT=Path(__file__).resolve().parents[2]


def graph_comparison(raw,directory=None):
    directory=Path(directory) if directory is not None else ROOT/'reports/graph_hypergraph'
    base=dict(rows=[],community_rows=[],inferential=False,refitted=False)
    path=directory/'structural_cache.npz';manifest=directory/'run_manifest.json'
    if not path.is_file() or not manifest.is_file():return dict(base,status='UNAVAILABLE_FROZEN_ARTIFACTS')
    m=json.loads(manifest.read_text(encoding='utf-8'));expected=m.get('artifacts',{}).get(path.name,{}).get('sha256')
    actual=sha256(path.read_bytes()).hexdigest()
    if expected!=actual:return dict(base,status='UNAVAILABLE_HASH_MISMATCH')
    rows=[];communities=[];endpoints=m['search_space']['endpoints']
    with np.load(path,allow_pickle=False) as cache:
        for row in raw['intervals']:
            if row['location']!='rolling' or row['window']!=104 or row['end'] not in endpoints:continue
            i=endpoints.index(row['end']);a=cache['adjacency_W104'][i]
            strength=a.sum(1);v=row['correlation']['eigenvectors'];loading=abs(v[:,0])
            rank_correlation=float(spearmanr(strength,loading).statistic) if np.std(strength)>0 and np.std(loading)>0 else np.nan
            top=np.argsort(-loading,kind='stable')[:6];graph_top=np.argsort(-strength,kind='stable')[:6]
            leverage=np.sum(v[:,:5]**2,axis=1)/5
            rows.append(dict(end=row['end'],window=104,spearman=rank_correlation,top6_overlap=len(set(top)&set(graph_top)),
                strength=strength.tolist(),loading_magnitude=loading.tolist(),top_loading_numbers=(top+1).tolist()))
            for k in (2,3):
                labels=cache[f'labels_W104_K{k}'][i]
                for label in sorted(set(labels.tolist())):
                    mask=labels==label;mass=float(leverage[mask].sum())
                    communities.append(dict(end=row['end'],window=104,communities=k,label=int(label),nodes=int(mask.sum()),
                        leading5_leverage_mass=mass,uniform_size_fraction=float(mask.mean()),excess=mass-float(mask.mean())))
    return dict(base,status='AVAILABLE_FROZEN_NO_REFIT',rows=rows,community_rows=communities,
        source=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),sha256=actual,
        limitation='Descriptive same-history comparison. Graph strength is 5*frequency; no independent predictive evidence.')


def plots(raw,null_spectra,graph,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory=Path(directory)
    names=['correlation.png','spectrum_mp.png','spectrum_iid.png','spectrum_fixed_margins.png',
           'leading_loadings.png','localization.png','rolling_largest.png','subspace_stability.png',
           'lagged_singular.png','covariance_sensitivity.png']
    if graph['rows']:names.append('graph_comparison.png')
    if any((directory/name).exists() for name in names):raise FileExistsError('Existing RMT plot bundle')
    directory.mkdir(parents=True,exist_ok=True);whole=raw['intervals'][0]['correlation'];a=whole['eigenvalues'];rank=np.arange(1,len(a)+1)
    def save(fig,name):
        fig.tight_layout();fig.savefig(directory/name,dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,6));im=ax.imshow(whole['matrix'],vmin=-.15,vmax=.15,cmap='coolwarm')
    ax.set(title='Number correlation (diagonal 1 clipped for inspection)',xlabel='Number index 0..44',ylabel='Number index 0..44');fig.colorbar(im,ax=ax);save(fig,names[0])
    mp=mp_reference(raw['draws'],len(a),variance=whole['trace']/len(a))
    fig,ax=plt.subplots(figsize=(9,5));ax.plot(rank,a,'o-',markersize=3,label='Real nontrivial spectrum')
    ax.axhspan(mp['lower'],mp['upper'],alpha=.15,label='Descriptive MP bulk; not a significance boundary')
    ax.set(xlabel='Descending mode',ylabel='Eigenvalue',title='Structural mode excluded');ax.legend(fontsize=8)
    inset=ax.inset_axes([.57,.32,.4,.38]);inset.hist(a,bins=12,density=True,alpha=.4);inset.plot(mp['grid'],mp['density']);inset.set_title('Spectral density / MP reference',fontsize=8);save(fig,names[1])
    for kind in ('iid','fixed_margins'):
        samples=null_spectra[kind][:,0,0,:len(a)];q=np.nanquantile(samples,[.025,.5,.975],axis=0)
        fig,ax=plt.subplots(figsize=(8,5));ax.fill_between(rank,q[0],q[2],alpha=.2,label='Pointwise 95% null envelope (not global test)')
        ax.plot(rank,q[1],label='Null median');ax.plot(rank,a,label='Real')
        ax.set(xlabel='Descending nontrivial mode',ylabel='Eigenvalue',title=f'Real vs {kind} spectrum');ax.legend(fontsize=8);save(fig,f'spectrum_{kind}.png')
    fig,ax=plt.subplots(figsize=(10,5))
    for j in range(5):ax.plot(np.arange(1,46),whole['eigenvectors'][:,j],'.-',label=f'Mode {j+1}')
    ax.set(xlabel='Number',ylabel='Canonical-sign loading',title='Leading loadings: signs have no semantic interpretation');ax.legend();save(fig,names[4])
    fig,ax=plt.subplots(figsize=(8,5));ax.plot(rank,whole['ipr'],'o-',label='IPR');ax.axhline(1/45,color='gray',linestyle='--',label='Uniform magnitude reference')
    ax.set(xlabel='Descending nontrivial mode',ylabel='IPR',title='Localization (degenerate-basis dependent)');ax.legend();save(fig,names[5])
    fig,ax=plt.subplots(figsize=(9,5))
    for window in raw['space']['windows']:
        rows=[r for r in raw['intervals'] if r['location']=='rolling' and r['window']==window]
        if rows:ax.plot([r['end'] for r in rows],[r['correlation']['eigenvalues'][0] for r in rows],'o-',label=f'W={window}')
    ax.set(xlabel='Last completed historical draw',ylabel='Largest nontrivial eigenvalue',title='Rolling correlation spectra');ax.legend();save(fig,names[6])
    fig,ax=plt.subplots(figsize=(9,5))
    for window in raw['space']['windows']:
        rows=[r for r in raw['stability'] if r['location']=='rolling_pair' and r['window']==window and r['rank']==5 and r['step']==1]
        if rows:ax.plot([r['end'] for r in rows],[r['overlap'] for r in rows],'o-',label=f'W={window}, r=5')
    ax.set(xlabel='Later window endpoint',ylabel='Projector overlap / rank',title='Adjacent leading-subspace stability (overlapping samples)');ax.legend();save(fig,names[7])
    fig,ax=plt.subplots(figsize=(8,5))
    for row in raw['lagged']:ax.plot(np.arange(1,len(row['singular_values'])+1),row['singular_values'],label=f"Lag={row['lag']}")
    ax.set(xlabel='Singular mode',ylabel='Singular value',title='Lagged cross-correlation: SVD, secondary');ax.legend();save(fig,names[8])
    fig,ax=plt.subplots(figsize=(8,5))
    for kind in ('correlation','covariance'):
        fit=raw['intervals'][0][kind];ax.plot(rank,fit['eigenvalues']/fit['trace'],label=kind)
    ax.set(xlabel='Descending mode',ylabel='Fraction of trace',title='Correlation vs covariance scaling (descriptive)');ax.legend();save(fig,names[9])
    if graph['rows']:
        fig,ax=plt.subplots(figsize=(8,5))
        for row in graph['rows']:ax.scatter(row['strength'],row['loading_magnitude'],s=9,alpha=.35)
        ax.set(xlabel='Frozen Graph W104 node strength (5*frequency)',ylabel='RMT leading loading magnitude',title='Matched historical windows; descriptive, Graph not refitted');save(fig,'graph_comparison.png')
    return names


def diagnostics(x,directory):
    from src.random_matrix_cli import dump
    x=research_matrix(x);directory=Path(directory).resolve()
    if len(x)!=1245 or not directory.is_relative_to((ROOT/'reports/random_matrix').resolve()):raise ValueError('Canonical historical RMT output required')
    files=['diagnostics.json','spectrum_rows.csv','mode_loadings.csv','interval_summary.csv','subspace_rows.csv',
           'lagged_spectrum.csv','lagged_loadings.csv','finite_sample_calibration.csv','graph_comparison.json','real_modes.npz']
    if any((directory/name).exists() for name in files) or (directory/'plots').exists():raise FileExistsError('Existing RMT diagnostics')
    raw=metric_vector(x);saved=pd.read_csv(directory/'full_metrics.csv')
    np.testing.assert_allclose(saved.value,raw['values'],equal_nan=True,rtol=1e-12)
    with np.load(directory/'null_metrics_full.npz') as f:null=f['values'];null_spectra=f['spectra']
    if null.shape!=(398,len(raw['keys'])) or null_spectra.shape!=(398,*raw['spectra'].shape):raise ValueError('Incomplete canonical null diagnostics')
    spectrum=[];loadings=[];intervals=[];vectors=[]
    for row in raw['intervals']:
        meta={k:row[k] for k in ('location','start','end','window')};pair=[]
        for kind in ('correlation','covariance'):
            fit=row[kind];pair.append(np.pad(fit['eigenvectors'],((0,0),(0,44-fit['nontrivial_dimension'])),constant_values=np.nan))
            intervals.append(dict(meta,kind=kind,largest=fit['eigenvalues'][0] if len(fit['eigenvalues']) else np.nan,
                smallest=fit['eigenvalues'][-1] if len(fit['eigenvalues']) else np.nan,entropy=fit['entropy'],effective_rank=fit['effective_rank'],
                trace=fit['trace'],leading_ipr=fit['ipr'][0] if len(fit['ipr']) else np.nan,active=int(fit['active'].sum()),structural_residual=fit['structural_residual']))
            for j,value in enumerate(fit['eigenvalues']):
                spectrum.append(dict(meta,kind=kind,mode=j+1,eigenvalue=value,ipr=fit['ipr'][j],participation_ratio=fit['pr'][j],
                    cumulative_variance=fit['cumulative_variance'][j],spacing_to_next=value-fit['eigenvalues'][j+1] if j+1<len(fit['eigenvalues']) else np.nan))
                if row['location']=='whole':
                    loadings.extend(dict(kind=kind,mode=j+1,number=i+1,loading=fit['eigenvectors'][i,j]) for i in range(45))
        vectors.append(pair)
    centered=[]
    for i,key in enumerate(raw['keys']):
        entry=dict(key=key,observed=raw['values'][i],**raw['metadata'][i])
        for kind,start in [('iid',0),('fixed_margins',199)]:
            a=null[start:start+199,i];a=a[np.isfinite(a)];median=float(np.median(a)) if len(a) else np.nan
            entry.update({f'{kind}_median':median,f'{kind}_centered':raw['values'][i]-median,
                          f'{kind}_percentile':float(np.mean(a<=raw['values'][i])) if len(a) else np.nan})
        centered.append(entry)
    lagrows=[];lagload=[]
    for row in raw['lagged']:
        for j,value in enumerate(row['singular_values']):
            lagrows.append(dict(lag=row['lag'],mode=j+1,singular_value=value,left_ipr=row['left_ipr'][j],right_ipr=row['right_ipr'][j]))
            if j<5:
                for side in ('left','right'):
                    lagload.extend(dict(lag=row['lag'],mode=j+1,side=side,number=i+1,loading=row[f'{side}_vectors'][i,j]) for i in range(45))
    subspace=[dict(row,principal_angles=json.dumps(row['principal_angles'].tolist())) for row in raw['stability']]
    graph=graph_comparison(raw);whole=raw['intervals'][0];corr=whole['correlation'];cov=whole['covariance']
    summary=dict(draws=1245,descriptive_only=True,space=raw['space'],graph=graph,
        whole={kind:{key:fit[key] for key in ('eigenvalues','ipr','pr','entropy','effective_rank','cumulative_variance','spacings','trace','structural_residual')}
               for kind,fit in [('correlation',corr),('covariance',cov)]},
        mp=mp_reference(1245,44,variance=corr['trace']/44),
        covariance_leading5_overlap=subspace_comparison(corr['eigenvectors'],cov['eigenvectors'],5),
        covariance_normalized_spectrum_max_difference=float(np.max(abs(corr['eigenvalues']/corr['trace']-cov['eigenvalues']/cov['trace']))),
        leading_degenerate_groups=degenerate_groups(corr['eigenvalues']),
        top_loading_numbers=(np.argsort(-abs(corr['eigenvectors'][:,0]),kind='stable')[:10]+1).tolist(),
        inferential_reference='global_null_comparison.csv; local centered statistics/percentiles and MP are not significance evidence')
    summary['plots']=plots(raw,{'iid':null_spectra[:199],'fixed_margins':null_spectra[199:]},graph,directory/'plots')
    for filename,rows in [('spectrum_rows.csv',spectrum),('mode_loadings.csv',loadings),('interval_summary.csv',intervals),
                          ('subspace_rows.csv',subspace),('lagged_spectrum.csv',lagrows),('lagged_loadings.csv',lagload),('finite_sample_calibration.csv',centered)]:
        pd.DataFrame(rows).to_csv(directory/filename,index=False)
    np.savez_compressed(directory/'real_modes.npz',vectors=np.array(vectors))
    dump(directory/'graph_comparison.json',graph);dump(directory/'diagnostics.json',summary)
    return summary
