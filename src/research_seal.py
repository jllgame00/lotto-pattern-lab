"""Fixed research seal. No CLI option can unseal draw1245 or later.

Read only header +1244 physical rows of the canonical single-line-row CSV.
The suffix is never handed to the CSV parser or included in provenance hashes.
"""
from hashlib import sha256
from io import StringIO
from pathlib import Path

import pandas as pd

LAST_OPEN_DRAW = 1244


def assert_open(frame, column='draw_no'):
    if column in frame and (pd.to_numeric(frame[column],errors='raise')>LAST_OPEN_DRAW).any():
        raise ValueError('Draw 1245 and later are sealed; research is limited to draws1..1244')


def _prefix_text(path):
    lines=[]
    with Path(path).open('r',encoding='utf-8-sig') as stream:
        for _ in range(LAST_OPEN_DRAW+1):
            line=stream.readline()
            if not line: break
            if not line.strip(): raise ValueError('Canonical CSV must have one nonempty physical row per draw')
            lines.append(line)
    return ''.join(lines)


def prefix_hash(path):
    """SHA256 of decoded open prefix, normalized newlines, not the full file."""
    return sha256(_prefix_text(path).encode('utf-8')).hexdigest()


def load_research_history(path):
    from src.collect.dataset import validate_history
    frame=pd.read_csv(StringIO(_prefix_text(path)))
    assert_open(frame)
    data=validate_history(frame)
    if frame.draw_no.tolist()!=list(range(1,len(frame)+1)):
        raise ValueError('Sealed research loader requires ascending contiguous canonical rows')
    return data
