"""Descriptive H18 segment exports and ten figures from stored evidence.

Detected penalized boundaries and best-single-split proposals remain separate.
Distance between historical segments is descriptive; it does not create a
recurring-regime predictor or establish a predictive capability.
"""
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.recurrence import research_matrix
from src.analysis.change_point import distribution_distance
from src.analysis.change_point_representation import shape_vector, block_frequency, SHAPE_FEATURES
from src.analysis.change_point_search import fit_prefix, FAMILIES
from src.backtest.symmetry import _validate_predictions, _decoded_list

REPORT_ROOT = Path(__file__).resolve().parents[2]/'reports'/'change_point'
PREFIXES = (800,900,1000,1100,1245)
DISTANCES = ('l1','js','cosine','max_shift')


def _directory(directory):
    directory = Path(directory).resolve()
    if not directory.is_relative_to(REPORT_ROOT.resolve()):
        raise ValueError('H18 output must stay under reports/change_point')
    return directory


def _clean(value):
    """Strict JSON: unsupported/nonfinite statistical values are explicit null."""
    if isinstance(value,dict):return {str(k):_clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [_clean(v) for v in value]
    if isinstance(value,np.generic):return _clean(value.item())
    if isinstance(value,float) and not np.isfinite(value):return None
    return value


def _json(value):
    return json.dumps(_clean(value),allow_nan=False,sort_keys=True)


def _summary(directory,x):
    summary = json.loads((directory/'real_summary.json').read_text(encoding='utf-8'))
    full = summary['full']
    if ('draws' in full and full['draws']!=len(x)) or (
            'representation_hash' in full and full['representation_hash']!=sha256(x.tobytes()).hexdigest()):
        raise ValueError('Stored full-search source hash/prefix mismatch')
    return summary


def _pair(x,left,right,unit):
    a,b = x[slice(*left)].mean(0),x[slice(*right)].mean(0)
    detail = distribution_distance(a,b)
    detail.update(before_support=int(left[1]-left[0]),after_support=int(right[1]-right[0]),
        before_start=int(left[0]+1),before_end=int(left[1]),
        after_start=int(right[0]+1),after_end=int(right[1]))
    if unit.startswith('number'):
        j = int(unit[6:])-1
        detail.update(before_rate=float(a[j]),after_rate=float(b[j]),rate_shift=float(b[j]-a[j]))
    return detail


def _temporal_rows(x, leaders):
    n = len(x); shapes = shape_vector(x)
    cuts = (0,415,830,1245) if n==1245 else (0,n//3,2*n//3,n)
    rows = []
    for family,leader in leaders.items():
        boundary = leader.get('boundary')
        if boundary is not None and not pd.isna(boundary):boundary = int(boundary)
        else:boundary = None
        unit = str(leader.get('unit','global'))
        for era,left,right in zip(('early','middle','recent'),cuts[:-1],cuts[1:]):
            rates = x[left:right].mean(0)
            row = dict(family=family,candidate_key=leader.get('key',family),
                kind=leader.get('kind','unspecified'),unit=unit,minimum=leader.get('minimum'),
                multiplier=leader.get('multiplier'),full_boundary=boundary,
                era=era,start=left+1,end=right,support=right-left,
                number_rates=_json(rates),shape_means=_json(shapes[left:right].mean(0)),
                candidate_frozen=True,diagnostic_only=True,era_reselected=False,
                before_support=0,after_support=0,**{key:None for key in DISTANCES})
            if unit.startswith('number'):
                row['number_rate'] = float(rates[int(unit[6:])-1])
            if boundary is not None and left<boundary<right:
                row.update(_pair(x,(left,boundary),(boundary,right),unit))
            rows.append(row)
    return rows


def diagnostics(x, directory, *, progress=None):
    """Export all exact-prefix fits and descriptive full-fit segment distances.

    Canonical prefixes are 800/900/1000/1100/1245. Short synthetic inputs use
    the available canonical prefixes plus their final endpoint. Nonadjacent
    comparisons retain the five smallest L1 distances per fit, with no search
    significance claim. Global full-search leader identities are held fixed
    across early/middle/recent eras; there is no era-specific reselection.
    """
    x = research_matrix(x); directory = _directory(directory)
    if len(x)<104:raise ValueError('H18 diagnostics require at least104 draws')
    summary = _summary(directory,x)
    prefixes = sorted({n for n in PREFIXES if n<=len(x)}|{len(x)})
    fit_rows=[];boundary_rows=[];adjacent=[];nonadjacent=[]
    for prefix in prefixes:
        fitted = fit_prefix(x[:prefix])['fits']
        for configuration,units in fitted.items():
            for unit,fit in units.items():
                base = dict(prefix=prefix,configuration=configuration,unit=unit,
                    minimum=fit['minimum'],multiplier=fit['multiplier'],penalty=fit['penalty'],
                    used_draws=fit['used_draws'],discarded_tail=fit['discarded_tail'])
                boundaries = fit['boundaries']; proposal = fit.get('proposal_boundary')
                fit_rows.append(dict(base,boundaries=_json(boundaries),segments=_json(fit['segments']),
                    has_change_point=bool(boundaries),boundary_count=len(boundaries),
                    gain=fit['gain'],cost=fit['cost'],objective=fit['objective'],
                    boundary_gains=_json(fit.get('boundary_gains',[])),
                    proposal_boundary=proposal,proposal_gain=fit.get('proposal_gain',0.),
                    proposal_is_detected=False))
                for kind,points in (('detected',boundaries),('proposal',[] if proposal is None else [proposal])):
                    for boundary in points or [None]:
                        boundary_rows.append(dict(base,kind=kind,boundary=boundary,
                            has_boundary=boundary is not None,diagnostic_only=True))
                if prefix!=len(x):continue
                for i,boundary in enumerate(boundaries):
                    adjacent.append(dict(base,kind='detected',boundary=boundary,
                        **_pair(x,fit['segments'][i],fit['segments'][i+1],unit)))
                if proposal is not None:
                    adjacent.append(dict(base,kind='proposal',boundary=proposal,
                        **_pair(x,(0,proposal),(proposal,fit['used_draws']),unit)))
                comparisons=[]
                for i,j in combinations(range(len(fit['segments'])),2):
                    if j-i<2:continue
                    comparisons.append(dict(base,kind='detected_segments',left_segment=i,right_segment=j,
                        diagnostic_only=True,**_pair(x,fit['segments'][i],fit['segments'][j],unit)))
                nonadjacent.extend(sorted(comparisons,key=lambda row:(row['l1'],row['left_segment'],row['right_segment']))[:5])
        if progress:progress(f'Diagnostics prefix {prefix}/{len(x)}')
    directory.mkdir(parents=True,exist_ok=True)
    tables = dict(segmentation_fits=pd.DataFrame(fit_rows),adjacent_segments=pd.DataFrame(adjacent),
        nonadjacent_segments=pd.DataFrame(nonadjacent),boundary_prefixes=pd.DataFrame(boundary_rows),
        temporal_eras=pd.DataFrame(_temporal_rows(x,summary['full'].get('leaders',{}))))
    # Empty detected-change sets are a valid statistical result and still have
    # readable schemas. Proposals do not manufacture detected segment pairs.
    schemas = dict(adjacent_segments=['prefix','configuration','unit','kind','boundary',*DISTANCES,
            'before_support','after_support'],
        nonadjacent_segments=['prefix','configuration','unit','kind','left_segment','right_segment',*DISTANCES],
        temporal_eras=['family','candidate_key','kind','unit','era','start','end','support'])
    paths = {}
    for name,table in tables.items():
        if table.empty and not len(table.columns):table = pd.DataFrame(columns=schemas.get(name,[]))
        paths[name] = directory/f'{name}.csv'; table.to_csv(paths[name],index=False)
    metadata = dict(draws=len(x),matrix_hash=sha256(x.tobytes()).hexdigest(),prefixes=prefixes,
        fit_rows=len(fit_rows),full_fits=sum(row['prefix']==len(x) for row in fit_rows),
        detected_boundaries=sum(row['has_boundary'] and row['kind']=='detected' for row in boundary_rows),
        boundary_convention='boundary b starts the next segment at draw b+1; segments are [start,end)',
        distances='45 raw number rates: L1, normalized JS divergence (nats), cosine similarity, maximum absolute shift',
        nonadjacent_policy='five smallest raw-rate L1 distances per full detected segmentation; descriptive only',
        era_policy='full-search leader and boundary fixed; no era reselection; absent within-era split is null',
        no_change_is_valid=True,proposal_is_detected=False,recurring_regime_predictor=False,
        leaders=summary['full'].get('leaders',{}),draw1246_used=False)
    paths['diagnostics_summary'] = directory/'diagnostics_summary.json'
    paths['diagnostics_summary'].write_text(_json(metadata)+'\n',encoding='utf-8')
    return paths


def _prediction_audit(x, rows):
    groups = {name:_validate_predictions(group,targets=range(901,len(x)+1),x=x)
        for name,group in rows.groupby('model')}
    if 'RegimeFrequencyModel' not in groups:raise ValueError('Stored regime predictions required')
    regime = groups['RegimeFrequencyModel']
    for row in regime.itertuples():
        boundary = row.last_change_point; length = row.current_segment_length
        if (not np.isfinite(boundary) or boundary!=int(boundary) or not 0<=boundary<row.target_draw-1 or
            length!=row.target_draw-1-boundary):
            raise ValueError('Stored current segment audit boundary/support mismatch')
        rates = np.asarray(json.loads(row.segment_rates),dtype=float)
        current = np.asarray(json.loads(row.current_rates),dtype=float)
        if (rates.shape!=(45,) or current.shape!=(45,) or not np.isfinite(current).all() or
            not ((current>=0)&(current<=1)).all() or
            not np.allclose(rates,x[int(boundary):row.target_draw-1].mean(0),rtol=0,atol=1e-12)):
            raise ValueError('Stored current segment audit rates mismatch')
    return groups


def plots(x, directory):
    """Render ten PNGs from completed diagnostic/null/prediction artifacts only."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    x = research_matrix(x); directory = _directory(directory)
    summary = _summary(directory,x)['full']
    metadata = json.loads((directory/'diagnostics_summary.json').read_text(encoding='utf-8'))
    if metadata['draws']!=len(x) or metadata['matrix_hash']!=sha256(x.tobytes()).hexdigest():
        raise ValueError('Stored diagnostic source prefix mismatch')
    fits = pd.read_csv(directory/'segmentation_fits.csv')
    boundaries = pd.read_csv(directory/'boundary_prefixes.csv')
    null = pd.read_csv(directory/'null_maxima.csv'); null = null[null.scope=='full']
    predictions = pd.read_csv(directory/'walk_forward_26'/'predictions.csv')
    groups = _prediction_audit(x,predictions)
    full = fits[fits.prefix==len(x)]
    if full.empty or fits.duplicated(['prefix','configuration','unit']).any():
        raise ValueError('Unique stored full-prefix fits required')
    for kind in ('iid','fixed_margins'):
        group = null[null.null_model==kind]
        if group.empty or group.replicate.duplicated().any() or not set(FAMILIES)<=set(group):
            raise ValueError('Stored own-max IID and fixed-margin evidence required')
    out = directory/'plots';out.mkdir(parents=True,exist_ok=True);paths=[]
    def save(fig,name):
        path=out/name
        fig.tight_layout();fig.savefig(path,dpi=140,bbox_inches='tight');plt.close(fig)
        paths.append(path)
    def detected_boundaries(unit,leader=None):
        selected=full[full.unit==unit]
        if leader is not None and all(key in leader for key in ('minimum','multiplier')):
            configuration=f'm{int(leader["minimum"])}_p{int(leader["multiplier"])}'
            selected=selected[selected.configuration==configuration]
        return sorted({int(boundary) for value in selected.boundaries for boundary in json.loads(value)})

    global_fits=full[full.unit.isin(('A','B13','B26','B52','C'))]
    fig,ax=plt.subplots(figsize=(12,6))
    labels=[]
    for i,row in enumerate(global_fits.itertuples()):
        labels.append(f'{row.unit}/{row.configuration}')
        ax.hlines(i,1,row.used_draws,color='lightgrey',lw=2)
        actual=json.loads(row.boundaries)
        ax.scatter(actual,[i]*len(actual),marker='|',s=80,color='#1f77b4',label='Detected penalized CP' if i==0 else None)
        if pd.notna(row.proposal_boundary):
            ax.scatter([row.proposal_boundary],[i],marker='x',s=22,color='#d95f02',label='Best single-split proposal' if i==0 else None)
    ax.set(yticks=range(len(labels)),yticklabels=labels,xlabel='Boundary draw b; next segment starts b+1',
        title='Global boundary timeline: detected changes and separate proposals')
    ax.tick_params(axis='y',labelsize=7)
    if labels:ax.legend(fontsize=8)
    save(fig,'change_point_timeline.png')

    cumulative=np.vstack([np.zeros(45),np.cumsum(x,axis=0)])
    endpoints=np.arange(1,len(x)+1);starts=np.maximum(0,endpoints-52)
    rolling=(cumulative[endpoints]-cumulative[starts])/(endpoints-starts)[:,None]
    leader=summary.get('leaders',{}).get('single_number',{})
    unit=str(leader.get('unit','number20'))
    if not unit.startswith('number') or not unit[6:].isdigit() or not 1<=int(unit[6:])<=45:
        unit='number20'
    strongest=int(unit[6:]);number_boundaries=detected_boundaries(unit,leader)
    fig,axes=plt.subplots(2,1,figsize=(12,9),sharex=True)
    im=axes[0].imshow(rolling.T,aspect='auto',interpolation='nearest',origin='lower',
        extent=(1,len(x),.5,45.5),cmap='viridis')
    axes[0].set(ylabel='Number',title='Number appearance rates in completed trailing windows of up to52 draws')
    fig.colorbar(im,ax=axes[0],label='Raw appearance rate')
    axes[1].plot(endpoints,rolling[:,strongest-1],label=f'Number {strongest}: trailing52 rate',lw=1.4)
    axes[1].axhline(6/45,color='grey',ls=':',label='IID marginal rate6/45')
    for boundary in number_boundaries:
        axes[1].axvline(boundary,color='#c44e52',ls='--',label=f'Detected CP b={boundary}')
    status='; no detected CP' if not number_boundaries else ''
    axes[1].set(xlabel='Completed draw',ylabel='Appearance rate',
        title=f'Strongest full-search number {strongest}: fixed candidate{status}')
    axes[1].legend(ncol=3,fontsize=8)
    save(fig,'number_frequency_heatmap.png')
    blocks=block_frequency(x,52)
    fig,ax=plt.subplots(figsize=(12,6))
    im=ax.imshow(blocks['rates'].T,aspect='auto',origin='lower',interpolation='nearest',cmap='viridis',
        extent=(0,blocks['used_draws'],.5,45.5))
    ticks=np.arange(0,len(blocks['ends']),max(1,len(blocks['ends'])//10))
    block_boundaries=detected_boundaries('B52')
    for i,boundary in enumerate(block_boundaries):
        ax.axvline(boundary,color='#c44e52',ls='--',lw=1,label='Detected B52 CP' if i==0 else None)
        ax.text(boundary,45.7,str(boundary),ha='center',va='bottom',fontsize=7)
    status='detected B52 boundaries across declared configurations' if block_boundaries else 'no detected B52 CP'
    ax.set(xticks=blocks['ends'][ticks],xlabel='Complete nonoverlapping 52-draw block endpoint',
        ylabel='Number',title=f'Block frequency: {status}; {blocks["discarded_tail"]} tail draws omitted')
    if block_boundaries:ax.legend(fontsize=8)
    fig.colorbar(im,ax=ax,label='Raw appearance rate');save(fig,'block_frequency_heatmap.png')

    shape=shape_vector(x);mean=shape.mean(0);std=shape.std(0)
    standardized=(shape-mean)/np.where(std>1e-12,std,1.)
    fig,ax=plt.subplots(figsize=(12,6))
    for j,name in enumerate(SHAPE_FEATURES):
        average=pd.Series(standardized[:,j]).rolling(52,min_periods=1).mean()
        ax.plot(endpoints,average,label=name,lw=1)
    shape_boundaries=detected_boundaries('C')
    for i,boundary in enumerate(shape_boundaries):
        ax.axvline(boundary,color='black',ls='--',lw=1,label='Detected C CP' if i==0 else None)
    status='detected C boundaries across declared configurations' if shape_boundaries else 'no detected C CP'
    ax.set(xlabel='Completed draw',ylabel='Prefix-standardized shape, rolling mean',
        title=f'Frozen seven shape coordinates; {status}')
    ax.legend(ncol=3,fontsize=8);save(fig,'shape_change_points.png')

    fig,ax=plt.subplots(figsize=(12,5));anchors=np.arange(13,len(x),13)
    number=boundaries[(boundaries.prefix==len(x)) & boundaries.unit.str.startswith('number')]
    for configuration,group in number.groupby('configuration',sort=False):
        for kind,style in (('detected','-'),('proposal',':')):
            counts=np.zeros(len(anchors),dtype=int)
            for _,unit in group[group.kind==kind].groupby('unit'):
                values=unit.boundary.dropna().to_numpy()
                if len(values):counts+=(abs(anchors[:,None]-values[None,:])<=13).any(1)
            ax.plot(anchors,counts,style,label=f'{configuration}/{kind}')
    ax.set(xlabel='Boundary anchor',ylabel='Distinct numbers with boundary within 13 draws',
        title='Boundary concentration; absence of detected CP contributes zero')
    if len(number):ax.legend(ncol=3,fontsize=7)
    save(fig,'boundary_concentration.png')

    fig,ax=plt.subplots(figsize=(12,6))
    selected=boundaries[boundaries.unit.isin(('A','B13','B26','B52','C'))]
    for kind,color,marker in (('detected','#1f77b4','|'),('proposal','#d95f02','x')):
        group=selected[(selected.kind==kind)&selected.boundary.notna()]
        ax.scatter(group.boundary,group.prefix,c=color,marker=marker,s=30,alpha=.6,label=kind)
    stability=summary.get('leaders',{}).get('stability',{})
    stability_unit=stability.get('unit')
    if isinstance(stability_unit,str) and stability_unit.startswith('number'):
        individual=boundaries[boundaries.unit==stability_unit]
        if all(key in stability for key in ('minimum','multiplier')):
            configuration=f'm{int(stability["minimum"])}_p{int(stability["multiplier"])}'
            individual=individual[individual.configuration==configuration]
        kind='proposal' if str(stability.get('kind','')).startswith('proposal') else 'detected'
        individual=individual[(individual.kind==kind)&individual.boundary.notna()]
        ax.scatter(individual.boundary,individual.prefix,c='#228833',marker='^',s=65,
            edgecolors='black',linewidths=.4,label=f'Frozen strongest stability leader: {stability_unit}/{kind}')
        if individual.empty:
            ax.text(.02,.03,f'{stability_unit}: no {kind} boundary in stored prefixes',
                transform=ax.transAxes,fontsize=8,color='#228833')
    ax.set(xlabel='Boundary location',ylabel='Available prefix cutoff',
        title='Prefix boundary stability: global fits and frozen strongest individual leader')
    ax.legend();save(fig,'prefix_stability.png')

    for kind,name in (('iid','iid_global_maxima.png'),('fixed_margins','fixed_margin_global_maxima.png')):
        fig,axes=plt.subplots(1,5,figsize=(16,4))
        group=null[null.null_model==kind]
        for ax,family in zip(axes,FAMILIES):
            values=group[family].to_numpy(dtype=float);values=values[np.isfinite(values)]
            ax.hist(values,bins=min(20,max(2,len(values))),color='#7896aa',alpha=.8)
            observed=summary['maxima'].get(family)
            if observed is not None:ax.axvline(observed,color='#c44e52',label='Observed own max')
            ax.set(title=family.replace('_','\n'),xlabel='Standardized complete-search maximum',ylabel='Replicates')
        axes[0].legend(fontsize=7)
        fig.suptitle(f'{kind}: independently rebuilt complete-search null maxima')
        save(fig,name)

    regime=groups['RegimeFrequencyModel']
    fig,axes=plt.subplots(2,1,figsize=(12,9))
    axes[0].plot(regime.target_draw,regime.current_segment_length,label='Current segment draws')
    axes[0].plot(regime.target_draw,regime.target_draw-1-regime.last_change_point,':',label='Audited cutoff minus last CP')
    axes[0].set(ylabel='Draws in current segment',title='Causal current segment: audited stored state at every target')
    axes[0].legend(fontsize=8)
    axes[0].set_xlabel('Historical prediction target')
    example=regime.iloc[-1];target=int(example.target_draw);cutoff=target-1
    numbers=np.arange(1,46)
    axes[1].plot(numbers,json.loads(example.segment_rates),'o-',ms=3,label='Current segment raw rate')
    axes[1].plot(numbers,x[:cutoff].mean(0),'--',label='Completed prefix rate')
    axes[1].plot(numbers,x[max(0,cutoff-52):cutoff].mean(0),':',label='Fixed52 rate')
    axes[1].plot(numbers,json.loads(example.current_rates),lw=1.2,label='Stored shrunk current rate')
    axes[1].set(xlabel='Number',ylabel='Appearance rate',xlim=(1,45),
        title=f'Historical target{target}; source cutoff{cutoff}; last CP{int(example.last_change_point)}; '
              f'current segment{int(example.current_segment_length)} draws')
    axes[1].legend(ncol=2,fontsize=8)
    save(fig,'current_segment_length.png')

    fig,axes=plt.subplots(2,1,figsize=(13,10))
    for name,group in groups.items():
        axes[0].plot(group.target_draw,group.hits.expanding().mean(),label=name)
    axes[0].axhline(.8,color='grey',ls=':',label='IID Top6 expectation .8')
    axes[0].set(xlabel='Historical prediction target',ylabel='Cumulative mean Top6 hits',
        title='Frozen historical rankings; no later configuration selection')
    examples=[name for name in ('RegimeFrequencyModel','GapLogistic') if name in groups]
    width=.8/len(examples)
    for index,name in enumerate(examples):
        row=groups[name].iloc[-1];ranking=_decoded_list(row.ranking)
        assigned={number:i+1 for i,number in enumerate(ranking)}
        offsets=(index-(len(examples)-1)/2)*width
        axes[1].bar(numbers+offsets,[46-assigned[n] for n in numbers],width=width,
            label=name,alpha=.8)
    actual=_decoded_list(regime.iloc[-1].actual)
    axes[1].scatter(actual,[46.5]*len(actual),marker='*',s=75,c='#c44e52',
        edgecolors='black',linewidths=.4,label='Actual winning numbers',zorder=4)
    axes[1].set(xlabel='Number',ylabel='Rank score (46 minus rank; higher is better)',
        title=f'Historical target{target}: stored 45-number rankings with actual winner marks',
        xticks=numbers,xlim=(.4,45.6),ylim=(0,49))
    axes[1].tick_params(axis='x',labelsize=7)
    axes[0].legend(ncol=3,fontsize=8);axes[1].legend(ncol=3,fontsize=8)
    save(fig,'historical_ranking_comparison.png')
    return paths
