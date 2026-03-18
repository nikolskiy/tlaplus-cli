import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator


class TlaUrls(BaseModel):
    stable: str
    nightly: str


class TlaConfig(BaseModel):
    jar_name: str
    urls: TlaUrls


class WorkspaceConfig(BaseModel):
    root: Path
    spec_dir: Path
    modules_dir: Path
    classes_dir: Path


class TlcConfig(BaseModel):
    java_class: str = "tlc2.TLC"
    overrides_class: str = "tlc2.overrides.TLCOverrides"


class JavaConfig(BaseModel):
    min_version: int = 11
    opts: list[str] = Field(default_factory=lambda: ["-XX:+IgnoreUnrecognizedVMOptions", "-XX:+UseParallelGC"])

    @model_validator(mode="before")
    @classmethod
    def check_env_opts(cls, data: Any) -> Any:
        if isinstance(data, dict):
            env_opts = os.environ.get("JAVA_OPTS")
            if env_opts:
                data["opts"] = env_opts.split()
        return data


class Settings(BaseModel):
    tla: TlaConfig
    workspace: WorkspaceConfig
    tlc: TlcConfig
    java: JavaConfig = Field(default_factory=JavaConfig)
