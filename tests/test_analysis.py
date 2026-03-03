import pandas as pd
import pytest

from magi.analysis import (
    run_cooccurrence,
    compute_alpha_diversity,
    compute_beta_diversity,
    run_differential,
)

_DUMMY_MATRIX = pd.DataFrame({"taxon_a": [1, 2], "taxon_b": [3, 4]})
_DUMMY_METADATA = pd.DataFrame({"group": ["control", "treatment"]})


def test_run_cooccurrence_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        run_cooccurrence(_DUMMY_MATRIX)


def test_compute_alpha_diversity_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        compute_alpha_diversity(_DUMMY_MATRIX)


def test_compute_beta_diversity_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        compute_beta_diversity(_DUMMY_MATRIX)


def test_run_differential_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        run_differential(_DUMMY_MATRIX, _DUMMY_METADATA)
