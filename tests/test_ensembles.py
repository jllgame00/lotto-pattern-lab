import json
import numpy as np
import pandas as pd
import pytest
from src.models.ensemble import normalize_scores, FrozenEnsemble


def predictions():
    records=[]
    for t in range(601,607):
        for name,reverse in [('a',False),('b',True)]:
            scores={n:float(n if reverse else 46-n) for n in range(1,46)}
            records.append(dict(target_draw=t,model=name,scores=json.dumps(scores),actual=json.dumps([1,2,3,4,5,6])))
    return pd.DataFrame(records)


def test_normalization_ties_and_range():
    constant={n:1. for n in range(1,46)}
    for method in ('rank','score'):
        np.testing.assert_allclose(normalize_scores(constant,method),.5)
    ranks=normalize_scores({n:n for n in range(1,46)},'rank')
    assert ranks[0]==0 and ranks[-1]==1
    with pytest.raises(ValueError): normalize_scores({1:1})


def test_ensemble_weights_frozen_strict_split():
    frame=predictions()
    e=FrozenEnsemble(['a','b']).select(frame[frame.target_draw<=603],development_end=603)
    assert e.weights[0]>=e.weights[1]
    before=e.weights.copy()
    scores=e.score(frame[frame.target_draw==604].drop(columns='actual'))
    assert set(scores)==set(range(1,46))
    np.testing.assert_allclose(e.weights,before)
    with pytest.raises(ValueError): e.score(frame[frame.target_draw==603])
    with pytest.raises(ValueError): FrozenEnsemble(['a','b']).select(frame,development_end=603)
    with pytest.raises(ValueError): e.select(frame[frame.target_draw<=603],development_end=603)


def test_development_selection_ignores_later_labels():
    frame=predictions(); train=frame[frame.target_draw<=603]
    e=FrozenEnsemble(['a','b']).select(train,development_end=603)
    later=frame[frame.target_draw==604].copy(); later.actual='[40,41,42,43,44,45]'
    assert e.score(later)==e.score(frame[frame.target_draw==604])
