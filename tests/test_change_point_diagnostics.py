"""Descriptive H18 artifacts preserve actual/proposed boundary distinctions."""
from hashlib import sha256
import importlib
import json

import numpy as np
import pandas as pd
import pytest

from src.analysis.spatiotemporal import iid_surrogate
from src.backtest.ranking import rank_metrics


def module():
    return importlib.import_module('src.analysis.change_point_diagnostics')


def fits(n):
    def one(boundaries):
        endpoints = [0,*boundaries,n]
        return dict(boundaries=boundaries,segments=list(map(list,zip(endpoints[:-1],endpoints[1:]))),
            gain=10.,cost=20.,objective=22.,penalty=2.,minimum=26,multiplier=1,
            boundary_gains=[5.]*len(boundaries),proposal_boundary=n//2,proposal_gain=3.,
            used_draws=n,discarded_tail=0,observations=n)
    return {'fits':{'m26_p1':{'A':one([52,104]),'number01':one([])}}}


def seed_summary(path,x):
    from src.analysis.change_point_search import FAMILIES
    full = dict(draws=len(x),representation_hash=sha256(x.tobytes()).hexdigest(),
        maxima={name:2. for name in FAMILIES},space={},leaders={
            'single_number':dict(key='frozen_number',unit='number01',kind='proposal_gain',
                minimum=26,multiplier=1,boundary=len(x)//2),
            'global_shift':dict(key='frozen_global',unit='A',kind='detected_l1',
                minimum=26,multiplier=1,boundary=52)})
    (path/'real_summary.json').write_text(json.dumps(dict(full=full,development=None)))


def test_diagnostics_exports_actual_fits_proposals_distances_and_fixed_candidates(tmp_path,monkeypatch):
    md = module();monkeypatch.setattr(md,'REPORT_ROOT',tmp_path)
    x = iid_surrogate(156,seed=191)
    seed_summary(tmp_path,x)
    monkeypatch.setattr(md,'fit_prefix',lambda past:fits(len(past)))
    paths = md.diagnostics(x,tmp_path)
    expected = {'segmentation_fits.csv','adjacent_segments.csv','nonadjacent_segments.csv',
        'boundary_prefixes.csv','temporal_eras.csv','diagnostics_summary.json'}
    assert expected <= {path.name for path in paths.values()}
    segments = pd.read_csv(tmp_path/'segmentation_fits.csv')
    assert len(segments)==2
    none = segments[segments.unit=='number01'].iloc[0]
    assert json.loads(none.boundaries)==[]
    assert none.proposal_boundary==78 and not none.has_change_point
    adjacent = pd.read_csv(tmp_path/'adjacent_segments.csv')
    assert set(adjacent.kind)=={'detected','proposal'}
    actual = adjacent[(adjacent.unit=='A') & (adjacent.kind=='detected')]
    assert actual.boundary.tolist()==[52,104]
    first = actual.iloc[0]
    assert first.before_support==52 and first.after_support==52
    a,b = x[:52].mean(0),x[52:104].mean(0)
    assert first.l1==pytest.approx(abs(a-b).sum())
    assert first.max_shift==pytest.approx(abs(a-b).max())
    nonadjacent = pd.read_csv(tmp_path/'nonadjacent_segments.csv')
    assert len(nonadjacent)==1 and nonadjacent.iloc[0].left_segment==0 and nonadjacent.iloc[0].right_segment==2
    temporal = pd.read_csv(tmp_path/'temporal_eras.csv')
    assert set(temporal.candidate_key)=={'frozen_number','frozen_global'}
    assert set(temporal.kind)=={'proposal_gain','detected_l1'}
    meta = json.loads((tmp_path/'diagnostics_summary.json').read_text())
    assert meta['matrix_hash']==sha256(x.tobytes()).hexdigest()
    assert meta['recurring_regime_predictor'] is False
    assert 'NaN' not in (tmp_path/'diagnostics_summary.json').read_text()


def test_canonical_diagnostics_uses_five_exact_completed_prefixes(tmp_path,monkeypatch):
    md = module();monkeypatch.setattr(md,'REPORT_ROOT',tmp_path)
    x = iid_surrogate(1245,seed=192);seed_summary(tmp_path,x)
    seen = []
    def observed(past):
        seen.append(len(past))
        assert np.array_equal(past,x[:len(past)])
        return fits(len(past))
    monkeypatch.setattr(md,'fit_prefix',observed)
    md.diagnostics(x,tmp_path)
    assert seen==[800,900,1000,1100,1245]
    temporal = pd.read_csv(tmp_path/'temporal_eras.csv')
    assert temporal[['era','start','end']].drop_duplicates().values.tolist()==[
        ['early',1,415],['middle',416,830],['recent',831,1245]]


def test_real_constant_search_exports_300_no_change_fits_and_readable_empty_tables(tmp_path,monkeypatch):
    md = module();monkeypatch.setattr(md,'REPORT_ROOT',tmp_path)
    x = np.zeros((156,45),dtype=bool);x[:,:6]=True
    seed_summary(tmp_path,x)
    md.diagnostics(x,tmp_path)
    fits_table=pd.read_csv(tmp_path/'segmentation_fits.csv')
    assert len(fits_table)==300 and fits_table.boundary_count.eq(0).all()
    assert fits_table.proposal_boundary.isna().all()
    assert pd.read_csv(tmp_path/'adjacent_segments.csv').empty
    assert pd.read_csv(tmp_path/'nonadjacent_segments.csv').empty
    assert set(fits_table.unit)=={f'number{n:02d}' for n in range(1,46)}|{'A','B13','B26','B52','C'}


def test_diagnostics_checks_output_scope_source_identity_and_research_seal(tmp_path,monkeypatch):
    md = module();monkeypatch.setattr(md,'REPORT_ROOT',tmp_path/'allowed')
    x = iid_surrogate(156,seed=193)
    with pytest.raises(ValueError,match='reports/change_point|output'):
        md.diagnostics(x,tmp_path/'elsewhere')
    allowed=tmp_path/'allowed';allowed.mkdir();seed_summary(allowed,x)
    summary=json.loads((allowed/'real_summary.json').read_text())
    summary['full']['representation_hash']='0'*64
    (allowed/'real_summary.json').write_text(json.dumps(summary))
    with pytest.raises(ValueError,match='source|hash|prefix'):
        md.diagnostics(x,allowed)
    with pytest.raises(ValueError):
        md.diagnostics(iid_surrogate(1246,seed=194),allowed)


def test_plots_render_ten_stored_figures_without_refitting(tmp_path,monkeypatch):
    md = module();monkeypatch.setattr(md,'REPORT_ROOT',tmp_path)
    from src.analysis.change_point_search import FAMILIES
    x = iid_surrogate(903,seed=195);seed_summary(tmp_path,x)
    monkeypatch.setattr(md,'fit_prefix',lambda past:fits(len(past)))
    md.diagnostics(x,tmp_path)
    null = pd.DataFrame([dict(scope='full',null_model=kind,replicate=i,
        **{family:float(i)/4 for family in FAMILIES}) for kind in ('iid','fixed_margins') for i in range(4)])
    null.to_csv(tmp_path/'null_maxima.csv',index=False)
    rows=[]
    for target in (901,902,903):
        actual=(np.flatnonzero(x[target-1])+1).tolist()
        for name in ('RegimeFrequencyModel','GapLogistic','RandomModel','Frequency26'):
            ranking=list(range(1,46));rates=x[target-53:target-1].mean(0).tolist()
            rows.append(dict(model=name,target_draw=target,feature_cutoff=target-1,training_cutoff=target-1,
                ranking=json.dumps(ranking),actual=json.dumps(actual),
                last_change_point=target-53,current_segment_length=52,
                segment_rates=json.dumps(rates),current_rates=json.dumps(rates),
                **rank_metrics(ranking,actual),
                **{f'pool_{k}':len(set(ranking[:k])&set(actual)) for k in (6,8,10,12,15)}))
    output=tmp_path/'walk_forward_26';output.mkdir()
    pd.DataFrame(rows).to_csv(output/'predictions.csv',index=False)
    def forbidden(*args,**kwargs):
        raise AssertionError('Plotting must not fit segmentations')
    monkeypatch.setattr(md,'fit_prefix',forbidden)
    paths=md.plots(x,tmp_path)
    assert len(paths)==10 and len(set(paths))==10
    assert all(path.suffix=='.png' and path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') for path in paths)
    # Stored audit rates are evidence, never silently recomputed for the plot.
    changed=pd.read_csv(output/'predictions.csv')
    changed.loc[changed.model=='RegimeFrequencyModel','segment_rates']=json.dumps([0.]*45)
    changed.to_csv(output/'predictions.csv',index=False)
    with pytest.raises(ValueError,match='segment|audit'):
        md.plots(x,tmp_path)
