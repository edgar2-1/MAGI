import pandas as pd
import pytest

from magi.unifier import standardize_outputs, build_feature_matrix, normalize


def test_standardize_outputs_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        standardize_outputs("input_dir", kingdom="bacteria", method="kraken2")


def test_build_feature_matrix_raises_not_implemented():
    with pytest.raises(NotImplementedError):
        build_feature_matrix("input_dir")


def test_normalize_raises_not_implemented():
    dummy = pd.DataFrame({"taxon_a": [1, 2], "taxon_b": [3, 4]})
    with pytest.raises(NotImplementedError):
        normalize(dummy)
