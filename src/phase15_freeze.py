"""draw1247_phase15_transformedspace preparation, never publication."""
from pathlib import Path
from src.phase11_freeze import PENDING
from src.backtest.transformed_space import load_selection,configuration_hash


def prepare_freeze(selection_path,archive,*,target=1247,protected=None):
    if type(target) is not int or target!=1247:raise ValueError('Only prospective target1247 permitted; never1246')
    archive=Path(archive)
    if not archive.is_dir() or not any(archive.rglob('*')):raise ValueError(PENDING)
    s=load_selection(selection_path)
    from src.phase14_freeze import prepare_freeze as verify
    prior=Path(__file__).resolve().parents[1]/'reports/graph_hypergraph/selected_configuration.json'
    verified=verify(prior,archive,target=target,protected=protected)
    return dict(verified,capability='draw1247_phase15_transformedspace',selection=s,selection_hash=configuration_hash(s),
        publication_executed=False,ready_for_publication=False,status='READY_FOR_EXPLICIT_IMPORT_AND_REFIT')
