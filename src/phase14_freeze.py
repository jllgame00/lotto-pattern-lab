"""draw1247_phase14_graph preparation gate; no publication in this phase."""
from pathlib import Path
from src.phase11_freeze import PENDING
from src.backtest.graph_hypergraph import load_selection,configuration_hash


def prepare_freeze(selection_path,archive,*,target=1247,protected=None):
    if type(target) is not int or target!=1247:raise ValueError('Only prospective target1247 is permitted; never1246')
    archive=Path(archive)
    if not archive.is_dir() or not any(archive.rglob('*')):raise ValueError(PENDING)
    selection=load_selection(selection_path)
    from src.phase11_freeze import prepare_freeze as verify_archive
    prior=Path(__file__).resolve().parents[1]/'reports/recurrence/selected_configuration.json'
    verified=verify_archive(prior,archive,target=target,protected=protected)
    return dict(verified,capability='draw1247_phase14_graph',selection=selection,selection_hash=configuration_hash(selection),
        publication_executed=False,ready_for_publication=False,status='READY_FOR_EXPLICIT_IMPORT_AND_REFIT')
