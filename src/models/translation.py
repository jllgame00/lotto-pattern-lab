"""Small, causal translation models; scores are ranking support, not probabilities."""
from dataclasses import asdict, dataclass
import numpy as np
from scipy.stats import rankdata
from src.analysis.spatiotemporal import binary_matrix,shift_scores,aligned,P


@dataclass(frozen=True)
class TranslationConfig:
    min_dt: int=1
    max_dt: int=52
    max_dn: int=15
    direction: str='both'
    top_rules: int=20
    prior_opportunities: float=100.
    min_history: int=104

    def __post_init__(self):
        if (self.direction not in ('both','positive','negative') or
            any(type(v) is not int or v<1 for v in (self.min_dt,self.max_dt,self.max_dn,self.top_rules,self.min_history)) or
            self.min_dt>self.max_dt or self.max_dn>44 or
            not np.isfinite(self.prior_opportunities) or self.prior_opportunities<=0):
            raise ValueError('Invalid translation configuration')


class TranslationModel:
    chain=False

    def __init__(self,**kwargs): self.config=TranslationConfig(**kwargs)

    def fit(self,x,*,cutoff):
        x=binary_matrix(x)
        if (type(cutoff) is not int or cutoff!=len(x) or not self.config.min_history<=cutoff<=1245 or
            cutoff<=self.config.max_dt or not np.all(x.sum(axis=1)==6)):
            raise ValueError('Fit requires exactly the permitted training prefix and sufficient history')
        self.training=x.copy(); self.training_cutoff=cutoff
        c=self.config; rows=shift_scores(x,max_dt=c.max_dt,max_dn=c.max_dn)
        rows=rows[(rows.delta_draw>=c.min_dt)&(rows.delta_number!=0)]
        if c.direction=='positive': rows=rows[rows.delta_number>0]
        if c.direction=='negative': rows=rows[rows.delta_number<0]
        candidates=[]
        for row in rows.itertuples():
            dt,dn=int(row.delta_draw),int(row.delta_number)
            opportunities,matches=int(row.valid_opportunities),int(row.observed_matches)
            if self.chain:
                source,destination=aligned(x,dt,dn,2)
                if not source.size: continue
                offset=0 if dn>0 else -2*dn
                middle=x[dt:dt+len(source),offset+dn:offset+dn+source.shape[1]]
                prior=source&middle
                opportunities=int(prior.sum()); matches=int((prior&destination).sum())
            posterior=(matches+c.prior_opportunities*P)/(opportunities+c.prior_opportunities)
            weight=max(0.,posterior-P)
            if weight>0:
                candidates.append(dict(delta_draw=dt,delta_number=dn,opportunities=opportunities,
                    matches=matches,shrunk_rate=posterior,weight=weight))
        self.rules=sorted(candidates,key=lambda r:(-r['weight'],r['delta_draw'],r['delta_number']))[:c.top_rules]
        return self

    def score_matrix(self,x,*,target):
        x=binary_matrix(x)
        if (type(target) is not int or target!=len(x)+1 or target>1246 or target<=self.training_cutoff or
            not np.all(x.sum(axis=1)==6) or not np.array_equal(x[:self.training_cutoff],self.training)):
            raise ValueError('Scoring needs the unchanged training prefix and only draws strictly before target')
        numerator=np.zeros(45); denominator=np.zeros(45)
        for rule in self.rules:
            dt,dn,weight=rule['delta_draw'],rule['delta_number'],rule['weight']
            numbers=np.arange(45); source=numbers-dn
            valid=(source>=0)&(source<45)&(target-dt>=1)
            if self.chain:
                older=numbers-2*dn
                valid &= (older>=0)&(older<45)&(target-2*dt>=1)
            indices=numbers[valid]
            present=x[target-dt-1,source[valid]].copy()
            if self.chain: present &= x[target-2*dt-1,older[valid]]
            numerator[indices]+=weight*present
            denominator[indices]+=weight
        support=np.divide(numerator,denominator,out=np.zeros(45),where=denominator>0)
        scores=P+(1-P)*support
        return {n+1:float(s) for n,s in enumerate(scores)}

    def configuration(self):
        return dict(model=type(self).__name__,version='phase6-v1',**asdict(self.config),
            minimum_predecessors=2 if self.chain else 1,
            score_definition='p+(1-p)*weighted fraction of eligible rules with observed source support; not probability')


class ChainModel(TranslationModel):
    chain=True


def combine_scores(*scores):
    """Predeclared equal-weight percentile ranks; exact ties receive average rank."""
    if not scores: raise ValueError('At least one component required')
    values=[]
    for s in scores:
        if set(s)!=set(range(1,46)) or not np.isfinite(list(s.values())).all(): raise ValueError('Need45 finite scores')
        values.append((rankdata([s[n] for n in range(1,46)],method='average')-1)/44)
    result=np.mean(values,axis=0)
    return {n+1:float(v) for n,v in enumerate(result)}
