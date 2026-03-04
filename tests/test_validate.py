import pytest

from magi.validate import (
    MAGIConfig,
    InputConfig,
    ProjectConfig,
    UnifierConfig,
    check_tools,
    validate_config,
)


def test_check_tools_returns_list():
    results = check_tools()
    assert isinstance(results, list)
    assert len(results) > 0


def test_check_tools_has_required_fields():
    results = check_tools()
    for r in results:
        assert "tool" in r
        assert "status" in r
        assert r["status"] in ("found", "missing")
        assert "required" in r


def test_check_tools_includes_optional():
    required_only = check_tools(include_optional=False)
    with_optional = check_tools(include_optional=True)
    assert len(with_optional) >= len(required_only)


def test_validate_config_missing_file(tmp_path):
    errors, warnings = validate_config(tmp_path / "nonexistent.yaml")
    assert len(errors) > 0
    assert "not found" in errors[0].lower()


def test_validate_config_empty_file(tmp_path):
    cfg = tmp_path / "empty.yaml"
    cfg.write_text("")
    errors, warnings = validate_config(cfg)
    assert len(errors) > 0


def test_validate_config_invalid_yaml(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text(": :\n  - invalid: [")
    errors, warnings = validate_config(cfg)
    assert len(errors) > 0


def test_validate_config_missing_required_keys(tmp_path):
    cfg = tmp_path / "partial.yaml"
    cfg.write_text("qc:\n  min_quality: 20\n")
    errors, warnings = validate_config(cfg)
    assert any("project" in e for e in errors)
    assert any("input" in e for e in errors)


def test_validate_config_valid(tmp_path):
    cfg = tmp_path / "good.yaml"
    cfg.write_text("project:\n  output_dir: results/\ninput:\n  reads: 'data/raw/*.fastq.gz'\n  platform: hifi\n")
    errors, warnings = validate_config(cfg)
    assert len(errors) == 0


def test_validate_config_invalid_platform(tmp_path):
    cfg = tmp_path / "bad_platform.yaml"
    cfg.write_text("project:\n  output_dir: results/\ninput:\n  reads: 'data/raw/*.fastq.gz'\n  platform: illumina\n")
    errors, warnings = validate_config(cfg)
    assert any("platform" in e for e in errors)


def test_validate_config_invalid_normalize(tmp_path):
    cfg = tmp_path / "bad_norm.yaml"
    cfg.write_text("project:\n  output_dir: results/\ninput:\n  reads: 'data/raw/*.fastq.gz'\n  platform: hifi\nunifier:\n  normalization: invalid\n")
    errors, warnings = validate_config(cfg)
    assert any("normalize" in e.lower() for e in errors)


# ---- Pydantic schema tests ----


def test_magi_config_valid_minimal():
    config = MAGIConfig(project=ProjectConfig(), input=InputConfig())
    assert config.project.output_dir == "results/"


def test_magi_config_with_platform():
    config = MAGIConfig(project=ProjectConfig(), input=InputConfig(platform="hifi"))
    assert config.input.platform == "hifi"


def test_magi_config_invalid_platform():
    with pytest.raises(Exception):
        MAGIConfig(project=ProjectConfig(), input=InputConfig(platform="illumina"))


def test_magi_config_invalid_normalize():
    with pytest.raises(Exception):
        MAGIConfig(
            project=ProjectConfig(),
            input=InputConfig(),
            unifier=UnifierConfig(normalization="invalid"),
        )


def test_magi_config_allows_extra_fields():
    config = MAGIConfig(
        project=ProjectConfig(),
        input=InputConfig(),
        custom_field="value",
    )
    assert config.custom_field == "value"


def test_validate_actual_default_config():
    """Validate that the actual default_config.yaml passes validation."""
    import os
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "default_config.yaml")
    if os.path.exists(config_path):
        errors, warnings = validate_config(config_path)
        assert len(errors) == 0, f"Default config has errors: {errors}"
