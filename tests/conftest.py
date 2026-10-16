import pandas as pd
import pytest
import shutil
import uuid
from pathlib import Path


@pytest.fixture
def tmp_path():
    """Use inherited ACLs: Windows sandbox cannot reopen mode-0700 directories."""
    root = Path(__file__).resolve().parent / '.tmp'
    path = root / uuid.uuid4().hex
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        if path.resolve().is_relative_to(root.resolve()):
            shutil.rmtree(path)


@pytest.fixture
def history():
    # Synthetic fixture only; never written to the canonical historical dataset.
    rows = []
    for i in range(1, 13):
        numbers = [1, 2, 3, 4, 5, 6] if i in (1, 3, 4, 8) else [7, 8, 9, 10, 11, 12]
        rows.append(dict(draw_no=i,
                         draw_date=(pd.Timestamp('2002-12-07') + pd.Timedelta(weeks=i-1)).strftime('%Y-%m-%d'),
                         **{f'num{j}': n for j, n in enumerate(numbers, 1)}, bonus=45))
    return pd.DataFrame(rows)
