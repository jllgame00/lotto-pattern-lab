"""Rebuild the complete H25 battery for IID and scope-conditional histories."""
from hashlib import sha256
import json
import numpy as np
from .spatiotemporal import iid_surrogate,constrained_surrogate
from .randomness_battery import TRACKS,SCOPES,scope_histories,metric_vector,track_view


def inventory_hash(raw):
    payload=dict(keys=raw['keys'],orientations=raw['orientations'],space=raw['space'])
    return sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()


def null_search(x,*,replicates=199,seed=260042,progress=None):
    actual=scope_histories(x)
    if type(replicates) is not int or replicates<1:raise ValueError('Positive replicate count required')
    rows=[]
    for track_code,track in enumerate(TRACKS):
        for i in range(replicates):
            row=dict(track=track,replicate=i,scopes={})
            for scope_id,scope in enumerate(SCOPES):
                source=actual[scope];n=len(source)
                child=int(np.random.SeedSequence([seed,track_code,i,scope_id,n]).generate_state(1)[0])
                null=iid_surrogate(n,seed=child) if track=='iid' else constrained_surrogate(source,seed=child)
                raw=track_view(metric_vector(null),track)
                row['scopes'][scope]=dict(seed=child,raw_values=raw['values'],units=len(raw['keys']),
                    rebuilt=True,inventory_hash=inventory_hash(raw),representation_hash=raw['representation_hash'],
                    row_six=bool((null.sum(1)==6).all()),
                    margins_preserved=bool(np.array_equal(source.sum(0),null.sum(0))) if track!='iid' else None,
                    triple_support=raw['details']['triple_support'])
            rows.append(row)
            if progress:progress(row)
    return rows
