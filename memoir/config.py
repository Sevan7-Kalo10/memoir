"""Configuration model for memoir stores.

All config lives in a single memoirs.yaml at the store root.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class DomainConfig(BaseModel):
    name: str
    index: str
    always_load: bool = False


class DecayRule(BaseModel):
    days: Optional[int] = None  # None = never decays
    to: Optional[int] = None
    action: Optional[str] = None  # "archive"


class WeightConfig(BaseModel):
    decay: dict[int, DecayRule] = Field(default_factory=lambda: {
        5: DecayRule(days=None),
        4: DecayRule(days=60, to=3),
        3: DecayRule(days=30, to=2),
        2: DecayRule(days=60, to=1),
        1: DecayRule(days=90, action="archive"),
    })
    boost: dict = Field(default_factory=lambda: {
        "thresholds": [5, 15, 30],
        "cap": 5,
    })


class LoadingConfig(BaseModel):
    max_tokens: int = 8000
    trim_order: list[int] = [3, 4]
    fts5_fallback: bool = True
    fts5_limit: int = 8


class EvolutionConfig(BaseModel):
    continue_prior: bool = True
    archive_index: str = "archive/INDEX.md"


class StoreConfig(BaseModel):
    path: str = "."
    archive_dir: str = "archive"
    trigger_file: str = "triggers.md"


class MemoirConfig(BaseModel):
    store: StoreConfig = Field(default_factory=StoreConfig)
    domains: list[DomainConfig] = Field(default_factory=lambda: [
        DomainConfig(name="core", index="MEMORY.md", always_load=True),
    ])
    weight: WeightConfig = Field(default_factory=WeightConfig)
    loading: LoadingConfig = Field(default_factory=LoadingConfig)
    evolution: EvolutionConfig = Field(default_factory=EvolutionConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "MemoirConfig":
        from ruamel.yaml import YAML

        path = Path(path)
        yaml_dir = path.parent.resolve()
        yaml = YAML(typ="safe")
        raw = yaml.load(path.read_text(encoding="utf-8"))
        config = cls.model_validate(raw)

        # Resolve store.path relative to the config file's directory
        store_p = Path(config.store.path)
        if not store_p.is_absolute():
            config.store.path = str((yaml_dir / store_p).resolve())

        return config

    def to_yaml(self, path: str | Path) -> None:
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        data = self.model_dump(exclude_defaults=False)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

    def get_domain(self, name: str) -> DomainConfig | None:
        for d in self.domains:
            if d.name == name:
                return d
        return None

    @property
    def always_load_domains(self) -> list[DomainConfig]:
        return [d for d in self.domains if d.always_load]

    @property
    def store_path(self) -> Path:
        return Path(self.store.path)
