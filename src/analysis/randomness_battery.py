"""Frozen nine-family H25 battery:2200 IID units,2147 conditional units."""
from hashlib import sha256
from math import comb
import numpy as np
from scipy.stats import rankdata
from .recurrence import research_matrix
from .randomness_statistics import (LAGS,SHAPE_LAGS,SHAPE_NAMES,SHAPE_BINS,representations,shape_reference,
    lag_correlation,transition_g,word_g,conditional_difference,number_gap_statistics,run_lengths,
    overlap_statistics,pair_triple_counts,spacing_statistics,spectral_statistics,entropy_deficit,normalized_lz,
    pearson,likelihood_ratio)

FAMILIES=('marginal','serial','run_gap','overlap','shape_distribution','shape_temporal','relational','spacing','spectral_entropy')
TRACKS=('iid','fixed_margins')
SCOPES=('full','early','middle','recent')


def scope_histories(x):
    x=research_matrix(x)
    if len(x)!=1245:raise ValueError('Canonical battery requires exact1..1245')
    return dict(full=x,early=x[:415],middle=x[415:830],recent=x[830:1245])


def metric_vector(x):
    x=research_matrix(x);n=len(x)
    if n<64:raise ValueError('Frozen battery needs at least64 historical draws')
    r=representations(x);keys=[];families=[];orientations=[];metadata=[];values=[];b_mask=[]
    def add(family,label,value,orientation='upper',conditional=True,**meta):
        keys.append(f'{family}|{label}');families.append(family);orientations.append(orientation);values.append(float(value));b_mask.append(conditional)
        metadata.append(dict(family=family,statistic=label,orientation=orientation,track_b=conditional,**meta))
    counts=x.sum(0);expected=np.full(45,n*6/45);sd=np.sqrt(n*(6/45)*(39/45))
    for j,count in enumerate(counts):add('marginal',f'number{j+1:02d}',count,'two_sided',False,number=j+1)
    for name,v,o in [('chi_square',pearson(counts,expected),'upper'),('likelihood_ratio',likelihood_ratio(counts,expected),'upper'),
        ('dispersion',counts.var(),'upper'),('max_standardized',np.max(abs(counts-expected))/sd,'upper'),
        ('upper_tail5',np.sort(counts)[-5:].sum()/(6*n),'upper'),('lower_tail5',np.sort(counts)[:5].sum()/(6*n),'lower')]:
        add('marginal',name,v,o,False)
    lz=[]
    for j in range(45):
        s=x[:,j].astype(int);number=f'number{j+1:02d}'
        for lag in LAGS:add('serial',f'{number}|acf{lag}',abs(lag_correlation(s,lag)),number=j+1,lag=lag)
        add('serial',f'{number}|transition_g',transition_g(s),number=j+1)
        for L in (2,3):add('serial',f'{number}|word{L}_g',word_g(s,L),number=j+1,length=L)
        add('serial',f'{number}|conditional_difference',conditional_difference(s),number=j+1)
        gap=number_gap_statistics(s)
        for stat in ('absence','appearance','runs','gap_gof','gap_cv2'):
            add('run_gap',f'{number}|{stat}',gap[stat],'two_sided' if stat in ('runs','gap_cv2') else 'upper',number=j+1)
        concentration,flat=spectral_statistics(s)
        add('spectral_entropy',f'{number}|concentration13',concentration,number=j+1)
        add('spectral_entropy',f'{number}|flatness_deficit13',flat,number=j+1)
        for L in (2,3,4):add('spectral_entropy',f'{number}|entropy_deficit{L}',entropy_deficit(s,L),number=j+1,length=L)
        lz.append(normalized_lz(s))
    add('spectral_entropy','mean_normalized_lz78',np.mean(lz),'two_sided')
    overlap_details={}
    for lag in LAGS:
        o=overlap_statistics(x,lag);overlap_details[str(lag)]={k:v for k,v in o.items() if k!='overlaps'}
        for stat in ('mean','variance','jaccard','gof','maximum'):
            add('overlap',f'lag{lag}|{stat}',o[stat],'two_sided' if stat in ('mean','variance','jaccard') else 'upper',lag=lag)
    ref=shape_reference();shape=r['shape']
    for j,name in enumerate(SHAPE_NAMES):
        a=shape[:,j];prob=np.histogram(a,bins=SHAPE_BINS[j])[0]/n
        cdf_distance=np.mean((np.cumsum(prob)-np.cumsum(ref['probabilities'][j]))**2)
        add('shape_distribution',f'{name}|mean',a.mean(),'two_sided',name not in ('sum','odd_count'),feature=name)
        add('shape_distribution',f'{name}|variance',a.var(),'two_sided',feature=name)
        add('shape_distribution',f'{name}|cdf_distance',cdf_distance,feature=name)
    scalar=np.column_stack((shape,r['bands']));names=list(SHAPE_NAMES)+[f'band{i+1}' for i in range(5)]
    ranked=rankdata(scalar,axis=0)
    for j,name in enumerate(names):
        for lag in SHAPE_LAGS:add('shape_temporal',f'{name}|rank_acf{lag}',abs(lag_correlation(ranked[:,j],lag)),feature=name,lag=lag)
        side=(scalar[:,j]>=ref['median'][j]).astype(int) if j<7 else (scalar[:,j]>=2).astype(int)
        _,lengths=run_lengths(side)
        add('shape_temporal',f'{name}|transition_g',transition_g(side),feature=name)
        add('shape_temporal',f'{name}|longest_side_run',lengths.max(),feature=name)
        add('shape_temporal',f'{name}|side_runs',len(lengths),'two_sided',feature=name)
    pairs,pc,triples,tc=pair_triple_counts(x)
    for pair,value in zip(pairs,pc):
        add('relational',f'pair_{pair[0]+1:02d}_{pair[1]+1:02d}',value,'two_sided',numbers=(pair+1).tolist())
    p2=comb(6,2)/comb(45,2);p3=comb(6,3)/comb(45,3)
    add('relational','pair_dispersion',pearson(pc,np.full(len(pc),n*p2)))
    eligible=(tc>=5)&(n*p3>=1);triple_z=(tc-n*p3)/np.sqrt(n*p3*(1-p3))
    winner=int(np.argmax(np.where(eligible,triple_z,-np.inf))) if eligible.any() else None
    add('relational','supported_triple_max',float(triple_z[winner]) if winner is not None else 0.,
        support_min=5,expected_min=1)
    spacing=spacing_statistics(r['numbers'])
    for d,value in enumerate(spacing['counts'],1):add('spacing',f'difference{d:02d}',value,'two_sided',difference=d)
    add('spacing','opportunity_corrected_gof',spacing['difference_gof'])
    add('spacing','adjacent_gap_gof',spacing['adjacent_gof'])
    add('spacing','vector_concentration',spacing['concentration'],'two_sided')
    a=np.array(values);mask=np.array(b_mask,bool)
    if not np.isfinite(a).all() or len(keys)!=len(set(keys)):raise ValueError('Nonfinite/duplicate frozen battery unit')
    space=dict(cells=len(keys),family_units={f:families.count(f) for f in FAMILIES},
        conditional_cells=int(mask.sum()),conditional_family_units={f:int(np.sum((np.array(families)==f)&mask)) for f in FAMILIES if f!='marginal'},
        lags=list(LAGS),shape_lags=list(SHAPE_LAGS),shape_reference_seed=260001,shape_reference_size=65536,
        shape_bins=[b.tolist() for b in SHAPE_BINS],shape_names=list(SHAPE_NAMES),band_edges=[[1,9],[10,18],[19,27],[28,36],[37,45]],
        pair_candidates=990,triple_candidates=14190,triple_support_min=5,triple_expected_min=1,
        fft_bins=list(range(1,14)),entropy_blocks=[2,3,4],lz='one mean normalized LZ78')
    triple_detail=dict(eligible=int(eligible.sum()),expected=float(n*p3),
        numbers=(triples[winner]+1).tolist() if winner is not None else None,count=int(tc[winner]) if winner is not None else 0)
    return dict(draws=n,keys=keys,families=families,orientations=orientations,metadata=metadata,values=a,track_b_mask=mask,
        space=space,representation_hash=sha256(x.tobytes()).hexdigest(),
        details=dict(overlap=overlap_details,triple_support=triple_detail,number_counts=counts))


def track_view(raw,track):
    if track not in TRACKS:raise ValueError('IID or fixed_margins track required')
    mask=np.ones(len(raw['keys']),bool) if track=='iid' else np.asarray(raw['track_b_mask'])
    index=np.flatnonzero(mask)
    return dict(draws=raw['draws'],track=track,keys=[raw['keys'][i] for i in index],families=[raw['families'][i] for i in index],
        orientations=[raw['orientations'][i] for i in index],metadata=[raw['metadata'][i] for i in index],values=raw['values'][mask],
        space=raw['space'],representation_hash=raw['representation_hash'],details=raw['details'])
