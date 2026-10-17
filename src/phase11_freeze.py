"""Offline draw-1247 preparation gate; deliberately no publication in this phase."""
from pathlib import Path
import json
from src.backtest.recurrence import load_selection,configuration_hash

PENDING='PROSPECTIVE_PUBLICATION_PENDING_ARCHIVE_RESTORATION'


def prepare_freeze(selection_path,archive,*,target=1247,protected=None):
    """Validate a restored archive against supplied ORIGINAL evidence before refit.

    No history is fetched, no snapshot is published, and no archive is reconstructed.
    The later explicit import/refit/publication step must attest target availability.
    """
    if type(target) is not int or target!=1247: raise ValueError('Only prospective target 1247 is permitted')
    archive=Path(archive)
    if not archive.is_dir() or not any(archive.rglob('*')): raise ValueError(PENDING)
    if not protected: raise ValueError('Original prior-archive integrity evidence is required')
    from hashlib import sha256
    names=set(protected)
    if not all(any(n.startswith(f'phase{phase}/') for n in names) for phase in range(6,11)) or not any('/' not in n for n in names):
        raise ValueError('A complete prior Phase 5–10 archive and original hash inventory are required')
    root=archive.resolve()
    from src.freeze_artifacts import registry_rows,verify_freeze
    from src.phase6_freeze import verify_2d
    from src.phase7_artifacts import verify_gap3d
    from src.phase8_artifacts import verify_frequency
    from src.phase9_artifacts import verify_joint
    from src.phase10_artifacts import verify_number_space
    verifiers=[verify_freeze,verify_2d,verify_gap3d,verify_frequency,verify_joint,verify_number_space]
    snapshots=[]
    for phase,verify in zip(range(5,11),verifiers):
        directory=root if phase==5 else root/f'phase{phase}'
        registry=directory/'registry.csv'
        if not registry.is_file() or registry.relative_to(root).as_posix() not in protected:
            raise ValueError('A complete prior archive requires every original registry')
        entries=registry_rows(directory)
        if not entries or not any(int(r['target_draw'])==1246 and int(r['training_cutoff'])==1245 for r in entries):
            raise ValueError('A complete prior archive requires the original draw1246 records')
        for entry in entries:
            for field in ('snapshot_path','manifest_path','integrity_path'):
                p=(directory/entry[field]).resolve()
                if not p.is_relative_to(directory) or p.relative_to(root).as_posix() not in protected:
                    raise ValueError('A complete prior archive requires original artifact inventory coverage')
            snapshots.append((verify,directory/entry['snapshot_path']))
        reservations=list(directory.glob('*.reservation.json'))
        if not reservations or any(p.relative_to(root).as_posix() not in protected for p in reservations):
            raise ValueError('A complete prior archive requires original reservation evidence')
    for relative,expected in protected.items():
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('Prior archive integrity mismatch: '+relative)
    for verify,path in snapshots: verify(path)
    selection=load_selection(selection_path)
    return dict(status='READY_FOR_EXPLICIT_IMPORT_AND_REFIT',target_draw=1247,training_cutoff=1246,
        research_cutoff=1245,selection=selection,selection_hash=configuration_hash(selection),
        publication_executed=False,requires_explicit_verified_1246_import=True)
