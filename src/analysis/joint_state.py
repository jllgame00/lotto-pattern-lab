"""Causal categorical gap x W26 frequency state, without continuous4D geometry."""
import numpy as np
import pandas as pd
from src.analysis.gap3d import causal_states,GapEncoder
from src.analysis.frequency3d import frequency_states,FrequencyEncoder
from src.analysis.spatiotemporal import binary_matrix,lotto_matrix

GAP_LABELS=('LOW','MID','HIGH')
FREQUENCY_LABELS=('COLD','NEUTRAL','HOT')
LABELS=tuple(f'{g} x {f}' for g in GAP_LABELS for f in FREQUENCY_LABELS)

def combine_states(gap,frequency):
    gap=np.asarray(gap);frequency=np.asarray(frequency)
    if gap.shape!=frequency.shape or not np.isin(gap,[-1,0,1,2]).all() or not np.isin(frequency,[-1,0,1,2]).all():
        raise ValueError('Matching categorical states -1,0,1,2 required')
    return np.where((gap>=0)&(frequency>=0),3*gap+frequency,-1).astype(np.int16)

class JointEncoder:
    def fit(self,x,*,cutoff):
        x=binary_matrix(x)
        if type(cutoff) is not int or cutoff!=len(x) or not 26<cutoff<=1245: raise ValueError('Exact bounded training prefix required')
        gap,_,relative=causal_states(x);f={k:v[:-1] for k,v in frequency_states(x,26).items()}
        self.gap_encoder=GapEncoder().fit(gap[:-1],relative[:-1],cutoff=cutoff)
        self.frequency_encoder=FrequencyEncoder(26).fit(f,cutoff=cutoff);self.cutoff=cutoff
        return self

    def transform(self,x):
        x=binary_matrix(x)
        if len(x)>1245: raise ValueError('History beyond1245 forbidden')
        gap,_,relative=causal_states(x);f=frequency_states(x,26)
        gs=self.gap_encoder.transform(gap,relative);fs=self.frequency_encoder.transform(f)
        return dict(gap=gap,frequency_count=f['count'],gap_state=gs,frequency_state=fs,joint_state=combine_states(gs,fs))

    def configuration(self):
        return dict(version='pre-draw-joint-v1',training_cutoff=self.cutoff,window=26,
            mapping='joint=3*gap_state+frequency_state; either missing =>-1',labels=list(LABELS),
            gap=self.gap_encoder.configuration(),frequency=self.frequency_encoder.configuration(),missing_state=-1)

def state_table(history,*,cutoff):
    x=lotto_matrix(history,cutoff=cutoff);enc=JointEncoder().fit(x,cutoff=cutoff);f=enc.transform(x)
    return pd.DataFrame(dict(target_draw=np.repeat(np.arange(1,cutoff+1),45),feature_cutoff=np.repeat(np.arange(cutoff),45),
        number=np.tile(np.arange(1,46),cutoff),appeared_next=x.ravel().astype(int),**{k:v[:-1].ravel() for k,v in f.items()}))

def support_audit(table):
    known=table.joint_state>=0;total=len(table);wins=int(table.appeared_next.sum());rows=[]
    for state,label in enumerate(LABELS):
        group=table[table.joint_state==state];n=len(group);k=int(group.appeared_next.sum())
        rows.append(dict(joint_state=state,gap_state=state//3,frequency_state=state%3,label=label,
            observations=n,winning_sources=k,source_opportunities_before_geometry=k,
            percent_all_states=100*n/total,percent_winning_sources=100*k/wins,
            sparse_sources_lt100=k<100,known_state_observations=int(known.sum())))
    return pd.DataFrame(rows)
