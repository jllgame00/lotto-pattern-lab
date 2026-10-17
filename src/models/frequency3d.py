"""Frequency-only source-state rules; historical gap is never an input."""
import numpy as np
from src.analysis.frequency3d import frequency_states,FrequencyEncoder,WINDOWS
from src.analysis.frequency_search import conditional_frequency
from src.analysis.spatiotemporal import binary_matrix,aligned,P
from src.models.translation import TranslationModel

class FrequencyConditionedTranslationModel(TranslationModel):
    def __init__(self,*,window=26,representation='quantile',min_support=None,**kwargs):
        super().__init__(**kwargs)
        if type(window) is not int or window not in WINDOWS or representation not in ('quantile','count','rate','relative'):
            raise ValueError('Predeclared frequency window/representation required')
        self.window=window;self.representation=representation
        self.min_support=(20 if self.chain else 100) if min_support is None else min_support
        if type(self.min_support) is not int or self.min_support<1: raise ValueError('Positive support required')

    def fit(self,x,*,cutoff):
        x=binary_matrix(x);c=self.config
        if (type(cutoff) is not int or cutoff!=len(x) or not c.min_history<=cutoff<=1245 or
            cutoff<=max(c.max_dt,self.window) or not np.all(x.sum(axis=1)==6)):
            raise ValueError('Fit requires exact bounded past prefix with sufficient history')
        self.training=x.copy();self.training_cutoff=cutoff
        f={k:v[:-1] for k,v in frequency_states(x,self.window).items()}
        self.encoder=FrequencyEncoder(self.window).fit(f,cutoff=cutoff)
        states=self.encoder.transform(f,self.representation);count=self.encoder.count(self.representation)
        if not self.chain:
            rows=conditional_frequency(x,states,state_count=count,max_dt=c.max_dt,max_dn=c.max_dn,min_support=self.min_support).to_dict('records')
        else:
            rows=[]
            for dt in range(c.min_dt,c.max_dt+1):
                for dn in range(-c.max_dn,c.max_dn+1):
                    if not dn: continue
                    a,z=aligned(x,dt,dn,2)
                    if not a.size: continue
                    offset=max(0,-2*dn)
                    b=x[dt:dt+len(a),offset+dn:offset+dn+a.shape[1]]
                    sa=aligned(states,dt,dn,2)[0]
                    sb=states[dt:dt+len(a),offset+dn:offset+dn+a.shape[1]]
                    eligible=a&b&(sb>=0)&(sa==sb)
                    opportunities=np.bincount(sb[eligible],minlength=count)
                    matches=np.bincount(sb[eligible&z],minlength=count)
                    rows.extend(dict(delta_draw=dt,delta_number=dn,state=s,valid_opportunities=int(opportunities[s]),matches=int(matches[s])) for s in range(count))
        rules=[]
        for row in rows:
            dt,dn=int(row['delta_draw']),int(row['delta_number'])
            if not dn or dt<c.min_dt or (c.direction=='positive' and dn<0) or (c.direction=='negative' and dn>0): continue
            opportunities,matches=int(row['valid_opportunities']),int(row['matches'])
            if opportunities<self.min_support: continue
            rate=(matches+c.prior_opportunities*P)/(opportunities+c.prior_opportunities)
            if rate>P: rules.append(dict(delta_draw=dt,delta_number=dn,frequency_state=int(row['state']),
                opportunities=opportunities,matches=matches,shrunk_rate=rate,weight=rate-P))
        self.rules=sorted(rules,key=lambda r:(-r['weight'],r['delta_draw'],r['delta_number'],r['frequency_state']))[:c.top_rules]
        return self

    def _context(self,x,target):
        x=binary_matrix(x)
        if (type(target) is not int or target!=len(x)+1 or target>1246 or target<=self.training_cutoff or
            not np.all(x.sum(axis=1)==6) or not np.array_equal(x[:self.training_cutoff],self.training)):
            raise ValueError('Scoring requires unchanged training prefix, strictly before target')
        f=frequency_states(x,self.window)
        return x,f,self.encoder.transform({k:v[:-1] for k,v in f.items()},self.representation)

    def _support(self,x,states,target):
        numerator=np.zeros(45);denominator=np.zeros(45)
        for rule in self.rules:
            dt,dn,w=rule['delta_draw'],rule['delta_number'],rule['weight']
            numbers=np.arange(45);source=numbers-dn
            valid=(source>=0)&(source<45)&(target-dt>=1)
            if self.chain:
                older=numbers-2*dn;valid &= (older>=0)&(older<45)&(target-2*dt>=1)
            indices=numbers[valid]
            if not len(indices): continue
            state=rule['frequency_state']
            present=x[target-dt-1,source[valid]]&(states[target-dt-1,source[valid]]==state)
            if self.chain: present &= x[target-2*dt-1,older[valid]]&(states[target-2*dt-1,older[valid]]==state)
            numerator[indices]+=w*present;denominator[indices]+=w
        support=np.divide(numerator,denominator,out=np.zeros(45),where=denominator>0)
        return {n+1:float(v) for n,v in enumerate(P+(1-P)*support)},denominator

    def score_matrix(self,x,*,target):
        x,_,states=self._context(x,target)
        return self._support(x,states,target)[0]

    def explain_number(self,number,x,*,target):
        if type(number) is not int or not 1<=number<=45: raise ValueError('Number must be1..45')
        x,f,states=self._context(x,target);scores,denominator=self._support(x,states,target);rows=[]
        for rule in self.rules:
            dt,dn=rule['delta_draw'],rule['delta_number'];source=number-dn;older=number-2*dn
            if not 1<=source<=45 or target-dt<1: continue
            if self.chain and (not 1<=older<=45 or target-2*dt<1): continue
            active=bool(x[target-dt-1,source-1] and states[target-dt-1,source-1]==rule['frequency_state'])
            if self.chain: active &= bool(x[target-2*dt-1,older-1] and states[target-2*dt-1,older-1]==rule['frequency_state'])
            value=f['count'][target-dt-1,source-1]
            rows.append(dict(**rule,window=self.window,source_draw=target-dt,source_number=source,
                source_count=None if np.isnan(value) else float(value),active=active,
                contribution=float((1-P)*rule['weight']*active/denominator[number-1])))
        return dict(number=number,target_draw=target,window=self.window,training_cutoff=self.training_cutoff,
            score=scores[number],baseline=P,rules=rows)

    def configuration(self):
        return dict(super().configuration(),version='phase8-frequency3d-v1',window=self.window,
            representation=self.representation,min_support=self.min_support,destination_state_used=False,
            state_version='pre-draw-frequency-v1',condition='two same-state observed predecessors' if self.chain else 'observed source pre-draw frequency',
            bin_fit='training pre-states only; frozen between refits',gap_features_used=False)

class FrequencyConditionedChainModel(FrequencyConditionedTranslationModel):
    chain=True
