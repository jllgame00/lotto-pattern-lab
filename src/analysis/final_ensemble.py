"""H17 frozen rank-only selection; no new feature or underlying predictor."""
from itertools import combinations
import numpy as np

PROMOTED=('GapLogistic','GraphStructureModel','GapShapeModel','MirrorModel')
SPLITS={'development':(901,1015),'validation':(1016,1130),'final':(1131,1245)}


def split_panel(panel,scope):
    t=np.asarray(panel['targets'])
    if (t.ndim!=1 or len(t)==0 or not np.equal(t,t.astype(int)).all() or
            t.min()<901 or t.max()>1245 or len(np.unique(t))!=len(t)):
        raise ValueError('Unique historical targets901..1245 required')
    a,b=SPLITS[scope];mask=(t>=a)&(t<=b)
    if not np.array_equal(t[mask],np.arange(a,b+1)):raise ValueError('Exact chronological block required')
    return dict(targets=t[mask],ranks=np.asarray(panel['ranks'])[mask],actual=np.asarray(panel['actual'])[mask],names=list(panel['names']))


def combine_ranks(ranks,weights):
    r=np.asarray(ranks);w=np.asarray(weights,float)
    if (r.ndim!=3 or r.shape[-1]!=45 or w.shape!=(r.shape[1],) or
            not np.isfinite(w).all() or np.any(w<0) or not np.isclose(w.sum(),1) or
            not np.all(np.sort(r,axis=-1)==np.arange(1,46))):
        raise ValueError('Complete45 ranks and convex weights required')
    # Fixed numerical tie precision; never calibrated from evaluation outcomes.
    cost=np.round(np.einsum('nck,c->nk',(r-1)/44,w),12)
    ordering=np.argsort(cost,axis=1,kind='stable')
    return np.argsort(ordering,axis=1,kind='stable')+1


def templates(names):
    if tuple(names)!=PROMOTED:raise ValueError('Frozen four candidate identities/order required')
    result=[]
    for size in (2,3):
        for ids in combinations(range(4),size):
            local=[np.ones(size)/size]
            if size==2:local += [np.array(w) for w in ((.6,.4),(.4,.6),(.7,.3),(.3,.7))]
            else:local += [np.array([.5 if i==j else .25 for i in range(3)]) for j in range(3)]
            for variant,values in enumerate(local):
                weights=np.zeros(4);weights[list(ids)]=values
                result.append(dict(id=f's{size}_'+''.join(map(str,ids))+f'_w{variant}',weights=weights.tolist(),size=size,equal=variant==0))
    result.append(dict(id='equal_all',weights=[.25]*4,size=4,equal=True))
    return result


def metric_series(ranks,actual):
    r=np.asarray(ranks);a=np.asarray(actual)
    if r.ndim!=2 or r.shape!=a.shape or r.shape[1]!=45 or not np.all(a.sum(1)==6):
        raise ValueError('Matched ranks and six actual numbers per target required')
    out={'mean_winning_rank':(r*a).sum(1)/6}
    for k in (6,8,10,12,15):out[f'pool{k}']=((r<=k)&a.astype(bool)).sum(1)
    out['hits']=out['pool6']
    return out


def metrics(ranks,actual):
    a=metric_series(ranks,actual);n=len(ranks)
    out=dict(targets=n,avg_top6=float(a['hits'].mean()),mean_winning_rank=float(a['mean_winning_rank'].mean()))
    out.update({f'hits{i}':int((a['hits']==i).sum()) for i in range(7)})
    out.update({f'recall{k}':float(a[f'pool{k}'].mean()/6) for k in (6,10,15)})
    for k in (6,8,10,12,15):
        out[f'ge5_pool{k}']=int((a[f'pool{k}']>=5).sum())
        out[f'all6_pool{k}']=int((a[f'pool{k}']==6).sum())
    return out


def _correlation(a,b):
    aa=a-a.mean();bb=b-b.mean();den=np.linalg.norm(aa)*np.linalg.norm(bb)
    return float(np.dot(aa,bb)/den) if den>0 else None


def diversity(panel):
    r=panel['ranks'];rows=[]
    for i,left in enumerate(panel['names']):
        for j,right in enumerate(panel['names']):
            a,b=r[:,i],r[:,j];ma=metric_series(a,panel['actual']);mb=metric_series(b,panel['actual'])
            row=dict(left=left,right=right,spearman=float(np.mean(np.sum((a-23)*(b-23),axis=1)/7590)),
                winner_rank_error_correlation=_correlation(ma['mean_winning_rank'],mb['mean_winning_rank']),
                top6_hit_correlation=_correlation(ma['hits'].astype(float),mb['hits'].astype(float)))
            row.update({f'top{k}_overlap':float(np.mean(((a<=k)&(b<=k)).sum(1))) for k in (6,10,15)})
            rows.append(row)
    return rows


def _score_grid(panel,grid):
    correlations=np.array([[float(np.mean(np.sum((panel['ranks'][:,i]-23)*(panel['ranks'][:,j]-23),axis=1)/7590)) for j in range(4)] for i in range(4)])
    result=[]
    for spec in grid:
        values=metrics(combine_ranks(panel['ranks'],spec['weights']),panel['actual'])
        w=np.asarray(spec['weights']);pairweights=np.array([w[i]*w[j] for i,j in combinations(range(4),2)])
        corr=np.array([max(0,correlations[i,j]) for i,j in combinations(range(4),2)])
        redundancy=float(pairweights@corr/pairweights.sum()) if pairweights.sum() else 0.
        result.append(dict(spec,**values,normalized_loss=(values['mean_winning_rank']-1)/44,
            redundancy=redundancy,diversity_objective=(values['mean_winning_rank']-1)/44+.02*redundancy))
    return result


def _choose(rows,objective='mean_winning_rank'):
    return min(rows,key=lambda r:(round(r[objective],12),round(r['mean_winning_rank'],12),-r['avg_top6'],r['size'],r['id']))


def _spec(row):return {k:row[k] for k in ('id','weights','size','equal')}


def select_development(panel,grid=None):
    p=split_panel(panel,'development')
    if len(panel['targets'])!=115 or tuple(p['names'])!=PROMOTED:raise ValueError('Development only, frozen four inputs')
    grid=templates(p['names']) if grid is None else grid
    rows=_score_grid(p,grid);equal=[r for r in rows if r['equal']]
    single=[dict(id=name,size=1,**metrics(p['ranks'][:,i],p['actual'])) for i,name in enumerate(p['names'])]
    return dict(winner=_spec(_choose(rows)),ordinary=_spec(_choose(equal)),
        diversity=_spec(_choose(equal,'diversity_objective')),best_single=_choose(single)['id'],
        development_rows=rows,single_rows=single,development_end=1015,
        selection_metric='mean_winning_rank;higherTop6;fewerComponents;configurationID')


def validation_support(candidate,references):
    return all(candidate['mean_winning_rank']<r['mean_winning_rank']-1e-12 and
        candidate['avg_top6']>=r['avg_top6']-1e-12 for r in references)


def validate_selection(panel,selection):
    p=split_panel(panel,'validation')
    if len(panel['targets'])!=115 or selection['development_end']!=1015:raise ValueError('Validation only after development freeze')
    baseline=templates(p['names'])[-1]
    refs={name:metrics(p['ranks'][:,p['names'].index(name)],p['actual']) for name in dict.fromkeys(['GapLogistic',selection['best_single']])}
    refs['equal_all']=metrics(combine_ranks(p['ranks'],baseline['weights']),p['actual'])
    details={}
    for strategy in ('winner','ordinary','diversity'):
        spec=selection[strategy];m=metrics(combine_ranks(p['ranks'],spec['weights']),p['actual'])
        required=[r for name,r in refs.items() if name!=spec['id']]
        details[strategy]=dict(configuration=spec,metrics=m,passed=validation_support(m,required))
    passed=details['winner']['passed']
    return dict(passed=passed,selected=selection['winner'] if passed else baseline,
        development_winner=selection['winner'],best_single=selection['best_single'],
        references=refs,strategies=details,validation_end=1130,
        fallback='equal_all audit baseline; no promoted ensemble' if not passed else None)


def paired_interval(a,b,*,seed=270042,replicates=2000,block=26):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if a.ndim!=1 or a.shape!=b.shape or not len(a) or not np.isfinite(a-b).all():raise ValueError('Matched finite target pairs required')
    n=len(a);length=min(block,n);rng=np.random.default_rng(seed)
    indices=((rng.integers(0,n,(replicates,int(np.ceil(n/length))))[:,:,None]+np.arange(length))%n).reshape(replicates,-1)[:,:n]
    sample=(a-b)[indices].mean(1);q=np.quantile(sample,[.025,.975,.05/6,1-.05/6])
    return dict(difference=float((a-b).mean()),ci_low=float(q[0]),ci_high=float(q[1]),
        simultaneous_low=float(q[2]),simultaneous_high=float(q[3]),block=block,replicates=replicates)


def leave_one_out(panel,weights):
    full=combine_ranks(panel['ranks'],weights);base=metrics(full,panel['actual']);rows=[]
    for i,name in enumerate(panel['names']):
        if weights[i]<=0:continue
        w=np.asarray(weights,float).copy();w[i]=0
        if w.sum()==0:continue
        w/=w.sum();r=combine_ranks(panel['ranks'],w);m=metrics(r,panel['actual'])
        rows.append(dict(removed=name,weights=w.tolist(),**m,top6_change=m['avg_top6']-base['avg_top6'],
            winner_rank_change=m['mean_winning_rank']-base['mean_winning_rank'],
            spearman_with_full=float(np.mean(np.sum((r-23)*(full-23),axis=1)/7590))))
    return rows


def random_weight_templates(names,*,seed):
    result=templates(names);rng=np.random.default_rng(seed)
    for spec in result:
        if spec['id']=='equal_all':continue
        w=np.asarray(spec['weights']);ids=np.flatnonzero(w);w[ids]=rng.dirichlet(np.ones(len(ids)))
        spec.update(weights=w.tolist(),equal=False)
    return result


def placebo_panel(panel,*,seed):
    rng=np.random.default_rng(seed);r=panel['ranks'].copy()
    for t in range(len(r)):r[t]=r[t][:,rng.permutation(45)]
    return dict(panel,ranks=r)


def run_placebos(panel,*,replicates=199,progress=None):
    rows=[]
    for kind,seed in [('random_weight',270101),('random_candidate',270202)]:
        for i in range(replicates):
            child=int(np.random.SeedSequence([seed,i]).generate_state(1)[0])
            p=placebo_panel(panel,seed=child) if kind=='random_candidate' else panel
            grid=random_weight_templates(p['names'],seed=child) if kind=='random_weight' else None
            selected=select_development(split_panel(p,'development'),grid)
            gate=validate_selection(split_panel(p,'validation'),selected)
            row=dict(kind=kind,replicate=i,seed=child,gate_passed=gate['passed'],winner=selected['winner']['id'],
                selected_weights=gate['selected']['weights'],best_single=selected['best_single'])
            for scope in SPLITS:
                part=split_panel(p,scope);r=combine_ranks(part['ranks'],gate['selected']['weights'])
                win=combine_ranks(part['ranks'],selected['winner']['weights'])
                best=part['ranks'][:,part['names'].index(selected['best_single'])]
                m,b,wm=[metrics(v,part['actual']) for v in (r,best,win)]
                row[f'{scope}_rank_gain']=b['mean_winning_rank']-m['mean_winning_rank']
                row[f'{scope}_top6_gain']=m['avg_top6']-b['avg_top6']
                row[f'{scope}_winner_rank_gain']=b['mean_winning_rank']-wm['mean_winning_rank']
                # Failed gates never masquerade as a promoted placebo ensemble.
                row[f'{scope}_promoted_gain']=row[f'{scope}_rank_gain'] if gate['passed'] else 0.
            rows.append(row)
            if progress and (i+1)%25==0:progress(f'{kind} {i+1}/{replicates}')
    return rows
