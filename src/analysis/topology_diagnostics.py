"""H0 inspection aids and descriptive, equal-count topological state geometry."""
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from .recurrence import research_matrix
from .topology import H1_STATUS
from .topology_search import FAMILIES,SUMMARIES,metric_vector,standardize

ROOT=Path(__file__).resolve().parents[2]


def topological_states(raw):
    groups={}
    for cloud in raw['clouds']:
        if cloud['location']=='rolling':groups.setdefault((cloud['config'],cloud['window']),[]).append(cloud)
    states=[];pairs=[]
    for (config,w),clouds in groups.items():
        clouds=sorted(clouds,key=lambda c:c['end']);counts={c['points'] for c in clouds}
        if len(counts)!=1:raise ValueError('Topological state comparisons require equal point counts')
        a=np.array([[c['persistence'][s] for s in SUMMARIES] for c in clouds]);mean=a.mean(0);std=a.std(0)
        constant=std<1e-12;z=(a-mean)/np.where(constant,1.,std);z[:,constant]=0.
        for i,c in enumerate(clouds):states.append(dict(config=config,window=w,end=c['end'],points=c['points'],features=z[i].tolist(),raw_features=a[i].tolist()))
        for step in (1,2,4):
            for i in range(max(0,len(clouds)-step)):
                pairs.append(dict(config=config,window=w,first_end=clouds[i]['end'],end=clouds[i+step]['end'],step=step,
                    points=clouds[i]['points'],feature_distance=float(np.linalg.norm(z[i]-z[i+step]))))
    return dict(descriptive_only=True,scaler_scope='same config/W, all observed descriptive endpoints; not a predictive scaler',states=states,pairs=pairs)


def _frozen_table(path,manifest):
    if not path.is_file() or not manifest.is_file():return None,'MISSING',None
    payload=json.loads(manifest.read_text(encoding='utf-8'));expected=payload.get('artifacts',{}).get(path.name)
    if isinstance(expected,dict):expected=expected.get('sha256')
    digest=sha256(path.read_bytes()).hexdigest()
    if digest!=expected:return None,'HASH_MISMATCH',digest
    return pd.read_csv(path),'AVAILABLE',digest


def frozen_comparison(raw,root=ROOT):
    root=Path(root)
    rmt,rs,rhash=_frozen_table(root/'reports/random_matrix/interval_summary.csv',root/'reports/random_matrix/manifest.json')
    graph,gs,ghash=_frozen_table(root/'reports/graph_hypergraph/graph_rows.csv',root/'reports/graph_hypergraph/run_manifest.json')
    rrows=[];grows=[];correlations=[]
    if rmt is not None or graph is not None:
        for c in raw['clouds']:
            if c['location']!='rolling' or c['config']!='B_euclidean':continue
            base=dict(end=c['end'],topology_window=c['window'],points=c['points'],h0_longest=c['persistence']['longest'])
            if rmt is not None:
                a=rmt[(rmt.location=='rolling')&(rmt.kind=='correlation')&(rmt.window==c['window'])&(rmt.end==c['end'])]
                if len(a)==1:rrows.append(dict(base,rmt_largest=float(a.iloc[0].largest),rmt_effective_rank=float(a.iloc[0].effective_rank)))
            if graph is not None and c['window']==208:
                a=graph[(graph.W==104)&(graph.end==c['end'])]
                if len(a)==1:grows.append(dict(base,graph_window=104,graph_concentration=float(a.iloc[0].concentration)))
    for rows,reference in ((rrows,'RMT'),(grows,'Graph')):
        for w in sorted({r['topology_window'] for r in rows}):
            group=[r for r in rows if r['topology_window']==w]
            columns=('rmt_largest','rmt_effective_rank') if reference=='RMT' else ('graph_concentration',)
            a=np.array([r['h0_longest'] for r in group])
            for column in columns:
                b=np.array([r[column] for r in group])
                rho=float(spearmanr(a,b).statistic) if len(a)>=3 and np.std(a)>1e-12 and np.std(b)>1e-12 else None
                correlations.append(dict(reference=reference,window=w,statistic=column,n=len(a),spearman=rho))
    return dict(status='AVAILABLE_FROZEN_NO_REFIT' if rrows or grows else 'UNAVAILABLE_FROZEN_ARTIFACTS',
        rmt_status=rs,graph_status=gs,rmt_sha256=rhash,graph_sha256=ghash,rmt_rows=rrows,graph_rows=grows,
        correlations=correlations,refitted=False,inferential=False,
        limitation='Same-history descriptive correlation, not independent evidence. Graph W104 and topology W208 spans differ.')


def plots(raw,c,null_values,relations,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory=Path(directory);names=['distance_concentration.png','h0_barcode.png','h0_diagram.png',
        'global_iid.png','global_fixed_margins.png','summary_distributions.png','rolling_h0.png','state_trajectory.png']
    if relations['rmt_rows'] or relations['graph_rows']:names.append('graph_rmt_comparison.png')
    if any((directory/name).exists() for name in names):raise FileExistsError('Existing topology plots')
    directory.mkdir(parents=True,exist_ok=True);whole=[a for a in raw['clouds'] if a['location']=='whole'];z=standardize(raw,c)
    null_z=np.divide(null_values-c['mean'],c['std'],out=np.full_like(null_values,np.nan),where=c['eligible'][None,:])
    families=np.array(raw['families']);null_z[:,families=='h0_entropy']=abs(null_z[:,families=='h0_entropy']);split=len(null_z)//2
    def save(fig,name):
        fig.tight_layout();fig.savefig(directory/name,dpi=150);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4));labels=[a['config'] for a in whole]
    for ax,key,title in zip(axes,['nearest_median_ratio','coefficient_variation'],['Median nearest / pairwise median','Distance std / pairwise median']):
        ax.bar(labels,[a['distance_diagnostic'][key] for a in whole]);ax.tick_params(axis='x',rotation=35);ax.set_title(title)
    save(fig,names[0])
    selected=next(a for a in whole if a['config']=='B_euclidean');deaths=selected['persistence']['finite_intervals'][:,1]
    fig,ax=plt.subplots(figsize=(8,5));shown=deaths[-60:]
    ax.hlines(np.arange(len(shown)),0,shown);ax.set(xlabel='Distance / edge filtration radius',ylabel='Finite H0 bar',title='Whole shape cloud: top 60 bars shown; essential bar excluded');save(fig,names[1])
    fig,ax=plt.subplots(figsize=(7,5));ax.scatter(np.zeros(len(deaths)),deaths,s=8,alpha=.4)
    limit=max(float(deaths.max()),1.);ax.plot([0,limit],[0,limit],'--',color='gray');ax.set(xlabel='Birth',ylabel='Death',title='H0 finite diagram (all births 0); one essential component excluded');save(fig,names[2])
    for kind,start in [('iid',0),('fixed_margins',split)]:
        fig,axes=plt.subplots(2,2,figsize=(10,7))
        for ax,family in zip(axes.ravel(),FAMILIES):
            mask=families==family;a=np.nanmax(null_z[start:start+split,mask],axis=1);real=np.nanmax(z[mask])
            ax.hist(a,bins=15,alpha=.7,label='Own complete-search null max');ax.axvline(real,color='red',label='Real max');ax.set_title(family);ax.legend(fontsize=7)
        save(fig,f'global_{kind}.png')
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for ax,family in zip(axes.ravel(),FAMILIES):
        indices=[i for i,m in enumerate(raw['metadata']) if m['family']==family and m['location']=='whole'];positions=np.arange(len(indices))
        ax.plot(positions,z[indices],'o',label='Real pilot-standardized score')
        for kind,start,offset in [('iid',0,-.08),('fixed_margins',split,.08)]:
            qs=[]
            for i in indices:
                a=null_z[start:start+split,i];a=a[np.isfinite(a)]
                qs.append(np.quantile(a,[.025,.5,.975]) if len(a) else np.full(3,np.nan))
            q=np.array(qs).T;ax.errorbar(positions+offset,q[1],yerr=np.maximum(np.array([q[1]-q[0],q[2]-q[1]]),0),fmt='.',label=kind)
        ax.set(xticks=positions,xticklabels=labels,title=f'{family}: matched whole clouds');ax.tick_params(axis='x',rotation=35);ax.legend(fontsize=6)
    save(fig,names[5])
    fig,ax=plt.subplots(figsize=(9,5))
    for w in raw['space']['windows']:
        indices=[i for i,m in enumerate(raw['metadata']) if m['family']=='h0_longest' and m['config']=='B_euclidean' and m['window']==w]
        if indices:ax.plot([raw['metadata'][i]['end'] for i in indices],z[indices],'o-',label=f'W={w}: matched point-count null')
    ax.set(xlabel='Last historical draw',ylabel='Pilot-standardized H0 longest',title='Rolling shape persistence; raw sample-size effects calibrated');ax.legend(fontsize=8);save(fig,names[6])
    states=[a for a in topological_states(raw)['states'] if a['config']=='B_euclidean' and a['window']==416]
    fig,ax=plt.subplots(figsize=(7,5))
    if states:
        a=np.array([s['features'] for s in states]);ax.plot(a[:,0],a[:,1],alpha=.5)
        im=ax.scatter(a[:,0],a[:,1],c=[s['end'] for s in states]);fig.colorbar(im,ax=ax,label='Endpoint')
    ax.set(xlabel='Standardized longest',ylabel='Standardized total',title='Equal-count W416 shape states: descriptive, not an attractor');save(fig,names[7])
    if len(names)>8:
        fig,axes=plt.subplots(2,2,figsize=(11,8))
        for ax,w in zip(axes.ravel()[:3],(208,416,624)):
            group=[r for r in relations['rmt_rows'] if r['topology_window']==w]
            ax.scatter([r['rmt_effective_rank'] for r in group],[r['h0_longest'] for r in group]);ax.set(xlabel='Frozen RMT effective rank',ylabel='H0 longest',title=f'Same span/points W={w}')
        group=relations['graph_rows'];axes[1,1].scatter([r['graph_concentration'] for r in group],[r['h0_longest'] for r in group])
        axes[1,1].set(xlabel='Frozen Graph W104 concentration',ylabel='Shape W208 H0 longest',title='Same endpoint; different spans (descriptive)');save(fig,names[8])
    return names


def diagnostics(x,directory):
    from src.topology_cli import dump,load_calibration
    x=research_matrix(x);directory=Path(directory).resolve()
    if len(x)!=1245 or not directory.is_relative_to((ROOT/'reports/topology').resolve()):raise ValueError('Canonical topology output required')
    files=('diagnostics.json','cloud_summary.csv','h0_intervals.csv','mst_edges.csv','state_trajectory.csv',
        'state_recurrence.csv','finite_sample_calibration.csv','h0_attribution.json','graph_rmt_comparison.json')
    if any((directory/f).exists() for f in files) or (directory/'plots').exists():raise FileExistsError('Existing topology diagnostics')
    raw=metric_vector(x);c=load_calibration(directory,1245);saved=pd.read_csv(directory/'full_metrics.csv')
    np.testing.assert_allclose(saved.value,raw['values'],rtol=1e-12,equal_nan=True)
    with np.load(directory/'null_metrics_full.npz') as f:null=f['values']
    if null.shape!=(398,len(raw['keys'])):raise ValueError('Incomplete canonical null metrics')
    summaries=[];bars=[];edges=[]
    for cloud in raw['clouds']:
        meta={k:cloud[k] for k in ('config','location','window','start','end','points','cloud_index')};p=cloud['persistence']
        summaries.append(dict(meta,**{s:p[s] for s in SUMMARIES},**{k:v for k,v in cloud['distance_diagnostic'].items() if k!='point_count'},
            finite_intervals=len(p['finite_intervals']),essential_components=1,filtration_max=p['filtration_max']))
        bars.extend(dict(meta,birth=0.,death=float(death),essential=False) for death in p['finite_intervals'][:,1]);bars.append(dict(meta,birth=0.,death=None,essential=True))
        for a,b,death in p['edges']:
            edges.append(dict(meta,point_a=int(a),point_b=int(b),draw_a=int(cloud['point_draws'][int(a)]),draw_b=int(cloud['point_draws'][int(b)]),death=float(death)))
    centered=[]
    for i,key in enumerate(raw['keys']):
        row=dict(key=key,observed=raw['values'][i],eligible=bool(c['eligible'][i]),**raw['metadata'][i])
        for kind,start in [('iid',0),('fixed_margins',199)]:
            a=null[start:start+199,i];a=a[np.isfinite(a)];median=float(np.median(a)) if len(a) else np.nan
            row.update({f'{kind}_median':median,f'{kind}_centered':raw['values'][i]-median,
                        f'{kind}_percentile':float(np.mean(a<=raw['values'][i])) if len(a) else np.nan})
        centered.append(row)
    states=topological_states(raw);relations=frozen_comparison(raw)
    a=next(c for c in raw['clouds'] if c['location']=='whole' and c['config']=='A_jaccard');edge=a['persistence']['edges'][-1]
    ids=[int(a['point_draws'][int(v)]) for v in edge[:2]]
    attribution=dict(config='A_jaccard',draws=ids,numbers=[(np.flatnonzero(x[t-1])+1).tolist() for t in ids],death=float(edge[2]),
        limitation='MST ties are not unique; vertices are draws, not individual numbers. No unique persistent number group or attractor is claimed.')
    whole=[r for r in summaries if r['location']=='whole']
    summary=dict(draws=1245,space=raw['space'],h1_status=H1_STATUS,diagram_metrics_implemented=False,whole=whole,
        eligible_cells=int(c['eligible'].sum()),unsupported_keys=[key for i,key in enumerate(raw['keys']) if not c['eligible'][i]],
        states_descriptive_only=True,relations=relations,attribution=attribution,
        inferential_reference='global_null_comparison.csv; raw mixed sample sizes/metric units and local percentiles are not global evidence')
    summary['plots']=plots(raw,c,null,relations,directory/'plots')
    state_rows=[{k:v for k,v in s.items() if k not in ('features','raw_features')}|{f'z_{name}':s['features'][i] for i,name in enumerate(SUMMARIES)}|{f'raw_{name}':s['raw_features'][i] for i,name in enumerate(SUMMARIES)} for s in states['states']]
    for name,rows in [('cloud_summary.csv',summaries),('h0_intervals.csv',bars),('mst_edges.csv',edges),('state_trajectory.csv',state_rows),
                      ('state_recurrence.csv',states['pairs']),('finite_sample_calibration.csv',centered)]:pd.DataFrame(rows).to_csv(directory/name,index=False)
    dump(directory/'h0_attribution.json',attribution);dump(directory/'graph_rmt_comparison.json',relations);dump(directory/'diagnostics.json',summary)
    return summary
