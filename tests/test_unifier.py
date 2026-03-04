import pandas as pd
import pytest

from magi.unifier.standardize import standardize_outputs
from magi.unifier.matrix import build_feature_matrix
from magi.unifier.normalize import normalize


def test_standardize_kraken2_output(tmp_path):
    """Parse a Bracken/Kraken2 output file into standard format."""
    kreport = tmp_path / "sample1_bacteria.tsv"
    kreport.write_text(
        "name\ttaxonomy_id\ttaxonomy_lvl\tkraken_assigned_reads\tadded_reads\tnew_est_reads\tfraction_total_reads\n"
        "Escherichia coli\t562\tS\t100\t10\t110\t0.55\n"
        "Staphylococcus aureus\t1280\tS\t80\t10\t90\t0.45\n"
    )

    result = standardize_outputs(tmp_path, kingdom="bacteria", method="kraken2")

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == [
        "SampleID", "Kingdom", "Taxon", "NCBI_TaxID",
        "Rank", "Abundance", "Method",
    ]
    assert len(result) == 2
    assert result["Kingdom"].unique().tolist() == ["bacteria"]
    assert result["Method"].unique().tolist() == ["kraken2"]
    assert 562 in result["NCBI_TaxID"].values


def test_standardize_empty_dir_returns_empty_df(tmp_path):
    result = standardize_outputs(tmp_path, kingdom="bacteria", method="kraken2")
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_build_feature_matrix_from_standardized(tmp_path):
    """Build a sample x feature matrix from standardized TSVs."""
    std_file = tmp_path / "standardized_bacteria.tsv"
    df = pd.DataFrame({
        "SampleID": ["s1", "s1", "s2", "s2"],
        "Kingdom": ["bacteria"] * 4,
        "Taxon": ["E.coli", "S.aureus", "E.coli", "S.aureus"],
        "NCBI_TaxID": [562, 1280, 562, 1280],
        "Rank": ["species"] * 4,
        "Abundance": [0.6, 0.4, 0.3, 0.7],
        "Method": ["kraken2"] * 4,
    })
    df.to_csv(std_file, sep="\t", index=False)

    matrix = build_feature_matrix(tmp_path)

    assert isinstance(matrix, pd.DataFrame)
    assert matrix.shape == (2, 2)
    assert "E.coli" in matrix.columns
    assert "s1" in matrix.index.tolist()


def test_build_feature_matrix_raises_on_no_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_feature_matrix(tmp_path)


def test_normalize_clr():
    matrix = pd.DataFrame(
        {"taxon_a": [10, 20, 30], "taxon_b": [5, 15, 25]},
        index=["s1", "s2", "s3"],
    )
    result = normalize(matrix, method="clr")
    assert result.shape == matrix.shape
    row_sums = result.sum(axis=1)
    for s in row_sums:
        assert abs(s) < 1e-10


def test_normalize_relative():
    matrix = pd.DataFrame(
        {"taxon_a": [10, 20], "taxon_b": [30, 80]},
        index=["s1", "s2"],
    )
    result = normalize(matrix, method="relative")
    for _, row in result.iterrows():
        assert abs(row.sum() - 1.0) < 1e-10


def test_normalize_tss():
    matrix = pd.DataFrame(
        {"taxon_a": [10, 20], "taxon_b": [30, 80]},
        index=["s1", "s2"],
    )
    result = normalize(matrix, method="tss")
    for _, row in result.iterrows():
        assert abs(row.sum() - 1.0) < 1e-10


def test_normalize_relative_zero_row():
    """Relative normalization should handle all-zero rows without NaN."""
    matrix = pd.DataFrame(
        {"A": [0, 100], "B": [0, 50]},
        index=["empty", "normal"],
    )
    result = normalize(matrix, method="relative")
    assert not result.isna().any().any()
    assert (result.loc["empty"] == 0).all()
    assert abs(result.loc["normal"].sum() - 1.0) < 1e-10


def test_normalize_invalid_method():
    matrix = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match="Unknown normalization method"):
        normalize(matrix, method="invalid")


def test_standardize_preserves_underscored_sample_ids(tmp_path):
    """Sample IDs with underscores should be preserved."""
    kreport = tmp_path / "sample_01_bacteria.tsv"
    kreport.write_text(
        "name\ttaxonomy_id\ttaxonomy_lvl\tkraken_assigned_reads\tadded_reads\tnew_est_reads\tfraction_total_reads\n"
        "Escherichia coli\t562\tS\t100\t10\t110\t0.55\n"
    )

    result = standardize_outputs(tmp_path, kingdom="bacteria", method="kraken2")
    assert len(result) == 1
    assert result.iloc[0]["SampleID"] == "sample_01"
