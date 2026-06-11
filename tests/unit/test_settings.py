import os

from tlaplus_cli.config.schema import JavaConfig


def test_java_config_default_opts():
    """Default opts are set if JAVA_OPTS is not present."""
    if "JAVA_OPTS" in os.environ:
        del os.environ["JAVA_OPTS"]

    config = JavaConfig()
    assert "-XX:+UseParallelGC" in config.opts


def test_java_config_env_opts_overrides(monkeypatch):
    """JAVA_OPTS environment variable overrides the default opts."""
    monkeypatch.setenv("JAVA_OPTS", "-Xmx4G -Xms2G")

    # We must pass something to trigger the validator since it's a model_validator(mode="before")
    # Actually, pydantic calls it even for default instantiation if not careful,
    # but here it's called with 'data' which is the dict passed to __init__ or empty dict.

    config = JavaConfig()
    assert config.opts == ["-Xmx4G", "-Xms2G"]


def test_java_config_env_opts_empty(monkeypatch):
    """Empty JAVA_OPTS should be ignored (keep defaults)."""
    monkeypatch.setenv("JAVA_OPTS", "")
    config = JavaConfig()
    assert "-XX:+UseParallelGC" in config.opts


def test_java_config_explicit_opts_with_env(monkeypatch):
    """JAVA_OPTS should override even explicitly passed opts in model_validator(mode='before')."""
    monkeypatch.setenv("JAVA_OPTS", "-Xmx1G")
    config = JavaConfig(opts=["-Xmx2G"])
    assert config.opts == ["-Xmx1G"]
