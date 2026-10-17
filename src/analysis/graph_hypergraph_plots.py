"""H12 descriptive plots. Pictures do not replace complete-search inference."""
import json
import numpy as np
import pandas as pd
from src.analysis.graph_structure import graph,similarity,adjusted_rand
from src.analysis.hypergraph_structure import motif_diagnostic,binary_hyperedges,pairwise_overlap
from src.analysis.graph_hypergraph_search import ENDPOINTS
from src.recurrence_cli import dump


def plots(x,directory):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.backtest.graph_hypergraph import load_selection,construct,PRIMARY_MODELS
    out=directory/'plots';out.mkdir(exist_ok=True)
    real=json.loads((directory/'real_maxima.json').read_text());s=load_selection(directory/'selected_configuration.json')
    def save(name):
        plt.tight_layout();plt.savefig(out/name,dpi=150);plt.close()
    def matrix(a,title,name,labels=None):
        plt.figure(figsize=(8,7));plt.imshow(a,origin='lower',cmap='magma');plt.colorbar(label='Co-occurrence count')
        labels=np.arange(1,46) if labels is None else labels
        ticks=np.arange(0,45,4);plt.xticks(ticks,labels[ticks]);plt.yticks(ticks,labels[ticks]);plt.xlabel('Number');plt.ylabel('Number');plt.title(title);save(name)
    matrix(graph(x)['adjacency'],'Cumulative1..1245 (descriptive reference)','long_term_cooccurrence.png')
    W=s['models']['GraphStructureModel']['window']
    matrix(graph(x,window=W)['adjacency'],f'Descriptive recentW{W} ending1245','recent_window_matrix.png')
    c=real['leaders']['edge'];g=graph(x[:c['end']],window=c['W']);upper=np.triu_indices(45,1)
    expected=c['W']/66;z=(g['adjacency'][upper]-expected)/np.sqrt(expected*(1-1/66));chosen=np.argsort(-z,kind='stable')[:12]
    labels=[f'{upper[0][i]+1}-{upper[1][i]+1}' for i in chosen]
    plt.figure(figsize=(11,4));plt.bar(np.arange(len(chosen)),z[chosen]);plt.xticks(np.arange(len(chosen)),labels)
    plt.ylabel('IID-normalized count z (not local p)');plt.title(f"Strongest-edge windowW{c['W']} end{c['end']}");save('strongest_normalized_edges.png')
    c=real['leaders']['community'];a=np.array(c['first_labels']);b=np.array(c['second_labels'])
    order=np.lexsort((np.arange(45),a));g=graph(x[:c['first_end']],window=c['W'])
    matrix(g['adjacency'][np.ix_(order,order)],f"Community ordering K{c['K']},W{c['W']},end{c['first_end']}; ARI={c['value']:.3f}",
        'community_ordered_matrix.png',labels=order+1)
    dump(directory/'strongest_communities.json',dict(**c,communities_first=[(np.flatnonzero(a==k)+1).tolist() for k in sorted(set(a)) if k>=0],
        communities_second=[(np.flatnonzero(b==k)+1).tolist() for k in sorted(set(b)) if k>=0]))
    cache=np.load(directory/'structural_cache.npz');adjacent=[]
    for window in (26,52,104):
        matrices=cache[f'adjacency_W{window}'];labels=cache[f'labels_W{window}_K2']
        for j in range(1,len(ENDPOINTS)):
            adjacent.append(dict(W=window,end=ENDPOINTS[j],previous_end=ENDPOINTS[j-1],
                **similarity(matrices[j-1],matrices[j]),community_ari=adjusted_rand(labels[j-1],labels[j])))
    dynamic=pd.DataFrame(adjacent);dynamic.to_csv(directory/'adjacent_similarity.csv',index=False)
    fig,axes=plt.subplots(3,1,figsize=(11,8));grows=pd.read_csv(directory/'graph_rows.csv')
    for window,g in dynamic.groupby('W'):
        axes[0].plot(g.end,g.cosine,label=f'W{window}');axes[1].plot(g.end,g.community_ari,label=f'W{window}')
    for window,g in grows.groupby('W'):axes[2].plot(g.end,g.clustering,label=f'W{window}')
    for ax,label in zip(axes,['Adjacent raw cosine','Adjacent K2 ARI','Clustering threshold2']):ax.set_ylabel(label);ax.legend()
    axes[2].set_xlabel('Historical window endpoint');save('graph_stability_through_time.png')
    temporal=[]
    for family in ('edge','triple'):
        c=real['leaders'][family];numbers=c['numbers'];present=x[:,np.array(numbers)-1].all(1)
        for label,start,end in [('early',1,415),('middle',416,830),('recent',831,1245)]:
            d=motif_diagnostic(x[:end],numbers,window=end-start+1)
            temporal.append(dict(family=family,era=label,start=start,end=end,**d))
        for end in ENDPOINTS:
            d=motif_diagnostic(x[:end],numbers,window=c['W'])
            temporal.append(dict(family=family,era='rolling',start=end-c['W']+1,end=end,**d))
    dump(directory/'motif_temporal_diagnostics.json',temporal)
    c=real['leaders']['triple'];present=x[:,np.array(c['numbers'])-1].all(1);cumulative=np.r_[0,np.cumsum(present)]
    end=np.arange(c['W'],len(x)+1);count=cumulative[end]-cumulative[end-c['W']]
    plt.figure(figsize=(11,4));plt.plot(end,count,label=f"W{c['W']} count")
    plt.axhline(c['expected'],linestyle='--',color='grey',label='IID expected');plt.axvline(c['end'],color='red',alpha=.5)
    plt.title(f"Selected triple{c['numbers']}; support>=3; descriptive trace");plt.xlabel('Window endpoint');plt.ylabel('Occurrences');plt.legend();save('strongest_triple_motif.png')
    null=pd.read_csv(directory/'null_maxima.csv')
    for kind in ('iid','fixed_margins'):
        fig,axes=plt.subplots(1,5,figsize=(16,3))
        for ax,family in zip(axes,real['maxima']):
            ax.hist(null[null.null_model==kind][family],bins=18,color='steelblue');ax.axvline(real['maxima'][family],color='red')
            ax.set_title(family);ax.set_xlabel('Global maximum')
        fig.suptitle(f'Real(red) versus {kind}; complete-search maxima');save(f'real_vs_{kind}.png')
    rows=pd.read_csv(directory/'walk_forward_26/predictions.csv');examples={};fig,axes=plt.subplots(2,1,figsize=(12,6))
    vectors={};frequencies={}
    for ax,name in zip(axes,PRIMARY_MODELS):
        row=rows[(rows.model==name)&(rows.target_draw==1245)].iloc[0];scores=json.loads(row.scores);ranking=json.loads(row.ranking)
        model=construct(s['models'][name]).fit(x[:1244],cutoff=1244);reproduced=model.score_matrix(x[:1244],target=1245)
        if any(reproduced[n]!=scores[str(n)] for n in range(1,46)):raise ValueError('Historical score reproduction mismatch')
        examples[name]=dict(target=1245,structural_training_cutoff=1244,ranking=ranking,diagnostic=model.last_diagnostic)
        vectors[name]=np.array([reproduced[n] for n in range(1,46)])
        frequencies[name]=graph(x[:1244],window=s['models'][name]['window'])['frequency']
        ax.bar(np.arange(45),[scores[str(n)] for n in ranking]);ax.set_xticks(np.arange(45),ranking,fontsize=7)
        ax.set_title(f'{name}; historical target1245, only<=1244');ax.set_ylabel('Relational score')
    save('model_ranking_example.png');dump(directory/'historical_ranking_example.json',examples)
    fig,axes=plt.subplots(1,3,figsize=(13,4));f=frequencies['GraphStructureModel'];axes[0].scatter(f,5*f)
    axes[0].set_xlabel('Appearance count');axes[0].set_ylabel('Weighted strength =5xcount')
    for ax,name in zip(axes[1:],PRIMARY_MODELS):
        ax.scatter(frequencies[name],vectors[name]);ax.axhline(0,color='grey',linestyle=':')
        ax.set_title(name);ax.set_xlabel('Own window appearance count');ax.set_ylabel('Frequency-residual score')
    save('frequency_vs_relational_score.png')
    # Set similarity is a descriptive hyperedge diagnostic, not a Phase11 model.
    sets=binary_hyperedges(x);overlap=pairwise_overlap(x);matches=[]
    for recent in range(len(x)-26,len(x)):
        for older in range(recent-26):
            matches.append(dict(recent_draw=recent+1,older_draw=older+1,overlap=int(overlap['overlap'][recent,older]),
                jaccard=float(overlap['jaccard'][recent,older])))
    matches=sorted(matches,key=lambda r:(-r['overlap'],r['recent_draw'],r['older_draw']))[:25]
    dump(directory/'hyperedge_similarity_examples.json',dict(expected_iid_overlap=.8,matches=matches,
        inference=False,delay_state_model_implemented=False))
