"""H12 fixed-grid full searches, including frequency-controlled successors."""
from hashlib import sha256
import numpy as np
from src.analysis.recurrence import research_matrix
from src.analysis.spatiotemporal import iid_surrogate,constrained_surrogate
from src.analysis.graph_structure import (WINDOWS,graph,relational_features,residualize,
    adjusted_rand,similarity)
from src.analysis.hypergraph_structure import TRIPLES,subset_counts,continuation_scores

ENDPOINTS=tuple(range(104,1245,26))+(1244,)
FAMILIES=('edge','community','triple','persistence','successor')
UPPER=np.triu_indices(45,1)


def unit_residual(values,frequency):
    v=residualize(values,frequency);s=np.std(v)
    return v/s if s>1e-12 else np.zeros(45)


def correlation(a,b):
    a=np.asarray(a,float).ravel();b=np.asarray(b,float).ravel();a=a-a.mean();b=b-b.mean()
    norm=np.linalg.norm(a)*np.linalg.norm(b)
    return float(a@b/norm) if norm>1e-12 else 0.


def complete_search(x,*,endpoints=ENDPOINTS,windows=WINDOWS,communities=(2,3),details=True):
    x=research_matrix(x)
    if (not endpoints or list(endpoints)!=sorted(set(endpoints)) or
        any(type(e) is not int or not max(windows)<=e<len(x) for e in endpoints)):
        raise ValueError('Ordered endpoints must precede available successor, never1246')
    if not windows or any(w not in WINDOWS for w in windows) or len(set(windows))!=len(windows):raise ValueError('Declared windows required')
    if not communities or any(k not in (2,3) for k in communities) or len(set(communities))!=len(communities):raise ValueError('Declared communities required')
    maxima=dict.fromkeys(FAMILIES,0.);leaders={};grows=[];prows=[];crows=[];srows=[];arrays={}
    features={};outcomes={};frequencies={};nonoverlap_count=0
    def update(family,value,metadata):
        if family not in leaders or value>maxima[family]:maxima[family]=float(value);leaders[family]=dict(value=float(value),**metadata)
    for W in windows:
        graphs=[];labels={k:[] for k in communities};vectors=[];triple_tables=[]
        for end in endpoints:
            past=x[:end];g=graph(past,window=W);graphs.append(g)
            f=g['frequency'];frequencies.setdefault(W,[]).append(f);features_here={}
            for k in communities:
                r=relational_features(g,past[-1],communities=k);labels[k].append(r['labels'])
                if k==communities[0]:features_here.update(neighbor=r['neighbor'],clustering=r['clustering'])
                features_here[f'community_K{k}']=r['community']
            for support in (2,3):
                h=continuation_scores(past,window=W,support=support,shrinkage=5)
                features_here[f'hyper_support{support}']=unit_residual(h['raw_scores'],f)
            for name,values in features_here.items():features.setdefault((W,name),[]).append(values)
            # First next-outcome access occurs after all graph/hypergraph features.
            actual=x[end].astype(float);outcomes.setdefault(W,[]).append(residualize(actual,f))
            own=past.mean(0);recent=f/W
            for name,values in features_here.items():
                top=np.argsort(-values,kind='stable')[:6]
                if details:srows.append(dict(W=W,feature=name,endpoint=end,target_draw=end+1,
                    hits=int(actual[top].sum()),next_rate=float(actual[top].mean()),
                    own_expected_hits=float(own[top].sum()),recent_expected_hits=float(recent[top].sum()),
                    feature_frequency_correlation=correlation(values,f)))
            edge_z=(g['adjacency'][UPPER]-W/66)/np.sqrt(W/66*(1-1/66));index=int(edge_z.argmax())
            i,j=int(UPPER[0][index]),int(UPPER[1][index]);edge=float(edge_z[index])
            update('edge',edge,dict(W=W,end=end,numbers=[i+1,j+1],count=int(g['adjacency'][i,j]),expected=W/66,
                own_counts=[int(f[i]),int(f[j])]))
            motifs=subset_counts(past,window=W,size=3);counts=motifs['counts']
            if details:triple_tables.append(counts)
            probability=20/14190;z=(counts-W*probability)/np.sqrt(W*probability*(1-probability));supported=counts>=3
            m=int(np.argmax(np.where(supported,z,-np.inf))) if supported.any() else 0
            triple=float(z[m]) if supported.any() else 0.
            update('triple',triple,dict(W=W,end=end,numbers=(TRIPLES[m]+1).tolist(),count=int(counts[m]),
                expected=W*probability,lift=float(counts[m]/(W*probability)),supported=bool(supported.any())))
            vector=g['residual_adjacency'][UPPER].astype(float);norm=np.linalg.norm(vector)
            vectors.append(vector/norm if norm>1e-12 else np.zeros_like(vector))
            grows.append(dict(W=W,end=end,edge_score=edge,strongest_edge=[i+1,j+1],strongest_edge_count=int(g['adjacency'][i,j]),
                strongest_node=int(np.argmax(f)+1),max_strength=int(np.max(g['strength'])),
                density=float(g['density']),clustering=float(g['clustering']),triangles=int(g['triangles']),wedges=int(g['wedges']),
                concentration=float(g['concentration']),expected_concentration=float(g['expected_concentration']),
                triple_score=triple,strongest_triple=(TRIPLES[m]+1).tolist(),triple_count=int(counts[m]),supported_triples=int(supported.sum())))
        V=np.asarray(vectors);cosine=V@V.T
        for a in range(len(endpoints)):
            for b in range(a+1,len(endpoints)):
                if endpoints[b]-endpoints[a]<W:continue
                nonoverlap_count+=1;value=float(cosine[a,b])
                update('persistence',value,dict(W=W,first_end=endpoints[a],second_end=endpoints[b]))
                if details:prows.append(dict(W=W,first_end=endpoints[a],second_end=endpoints[b],residual_cosine=value))
                for k in communities:
                    first,second=labels[k][a],labels[k][b];shared=int(((first>=0)&(second>=0)).sum())
                    ari=adjusted_rand(first,second) if shared>=20 else 0.
                    update('community',ari,dict(W=W,K=k,first_end=endpoints[a],second_end=endpoints[b],shared_nodes=shared,
                        first_labels=first.tolist(),second_labels=second.tolist()))
                    if details:crows.append(dict(W=W,K=k,first_end=endpoints[a],second_end=endpoints[b],shared_nodes=shared,adjusted_rand=ari))
        if details:
            arrays[f'adjacency_W{W}']=np.array([g['adjacency'] for g in graphs])
            arrays[f'frequency_W{W}']=np.array([g['frequency'] for g in graphs])
            arrays[f'triple_counts_W{W}']=np.array(triple_tables)
            for k in communities:arrays[f'labels_W{W}_K{k}']=np.array(labels[k])
    successor_summary=[]
    for (W,name),values in features.items():
        values=np.asarray(values);target=np.asarray(outcomes[W]);value=correlation(values,target)
        update('successor',value,dict(W=W,feature=name,endpoints=list(endpoints),draws=len(endpoints),node_records=values.size))
        successor_summary.append(dict(W=W,feature=name,correlation=value,frequency_correlation=correlation(values,
            np.asarray(frequencies[W]))))
        if details:arrays[f'features_W{W}_{name}']=values
    space=dict(numbers=45,windows=list(windows),endpoints=list(endpoints),graphs=len(windows)*len(endpoints),
        pair_cells=len(windows)*len(endpoints)*990,triple_cells=len(windows)*len(endpoints)*14190,
        community_counts=list(communities),community_partitions=len(windows)*len(endpoints)*len(communities),
        community_stability_cells=nonoverlap_count*len(communities),persistence_cells=nonoverlap_count,
        successor_cells=len(features),successor_targets=len(endpoints),families=5,subset_support=3)
    return dict(maxima=maxima,leaders=leaders,space=space,graph_rows=grows if details else [],
        persistence_rows=prows,community_rows=crows,successor_rows=srows,successor_summary=successor_summary,
        arrays=arrays,representation_hash=sha256(x.tobytes()).hexdigest())


def _null_job(job):
    x,kind,code,i,seed,args=job
    child=int(np.random.SeedSequence([seed,code,i]).generate_state(1)[0])
    null=iid_surrogate(len(x),seed=child) if code==0 else constrained_surrogate(x,seed=child)
    result=complete_search(null,details=False,**args)
    return dict(null_model=kind,replicate=i,seed=child,rebuilt=True,space=result['space'],
        representation_hash=result['representation_hash'],changed_fraction=float((x!=null).mean()),**result['maxima'])


def null_search(x,*,replicates=199,seed=140042,search_args=None,workers=1,progress=None):
    x=research_matrix(x)
    if type(replicates) is not int or replicates<1 or type(workers) is not int or workers<1:raise ValueError('Positive counts required')
    jobs=[(x,k,c,i,seed,search_args or {}) for k,c in [('iid',0),('fixed_margins',1)] for i in range(replicates)]
    rows=[]
    def consume(iterator):
        for row in iterator:
            rows.append(row)
            if progress:progress(row)
    if workers==1:consume(map(_null_job,jobs))
    else:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=workers) as pool:consume(pool.map(_null_job,jobs))
    return rows


def compare_maxima(real,rows):
    output=[]
    for kind in ('iid','fixed_margins'):
        group=[r for r in rows if r['null_model']==kind]
        if not group:raise ValueError('Both null families required')
        for family in FAMILIES:
            values=np.array([r[family] for r in group]);observed=real['maxima'][family]
            exceed=int((values>=observed).sum());p=(1+exceed)/(len(values)+1)
            output.append(dict(null_model=kind,family=family,real_max=observed,null_mean=float(values.mean()),
                null_q95=float(np.quantile(values,.95)),exceedances=exceed,replicates=len(values),global_p=p,adjusted_p=min(1.,5*p)))
    return output
