"""config.yaml dosyasını yükler."""
from functools import lru_cache
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@lru_cache(maxsize=1)
def load_config(path: str | None = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def db_path(cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    p = Path(cfg["database"]["path"])
    return p if p.is_absolute() else PROJECT_ROOT / p
