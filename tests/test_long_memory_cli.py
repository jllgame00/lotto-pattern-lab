from pathlib import Path
import pytest
from src.long_memory_cli import guard, prospective_guard, canonical_matrix
from src.analysis.spatiotemporal import iid_surrogate


def test_output_and_prospective_protection(tmp_path):
    with pytest.raises(ValueError):guard(tmp_path)
    with pytest.raises(ValueError,match='1246'):prospective_guard(1246,tmp_path)
    with pytest.raises(ValueError,match='ARCHIVE'):prospective_guard(1247,tmp_path)
    archive=tmp_path/'archive';archive.mkdir()
    with pytest.raises(ValueError,match='ARCHIVE'):prospective_guard(1247,archive)
    (archive/'placeholder').write_text('not a verified archive')
    with pytest.raises(ValueError,match='MODEL'):prospective_guard(1247,archive)


def test_exact_research_cutoff():
    assert canonical_matrix(iid_surrogate(1245,seed=21)).shape==(1245,45)
    with pytest.raises(ValueError):canonical_matrix(iid_surrogate(1246,seed=21))
    with pytest.raises(ValueError):canonical_matrix(iid_surrogate(900,seed=21))


def test_cli_registration():
    from src.cli import _parser
    args=_parser().parse_args(['long-memory','benchmark'])
    assert args.action=='benchmark' and args.surrogates==199
    with pytest.raises(SystemExit):_parser().parse_args(['long-memory','publish'])
