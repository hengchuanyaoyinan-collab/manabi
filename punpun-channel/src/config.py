"""設定読み込み。
config/*.json と .env をまとめてアクセスしやすくする。
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

load_dotenv(PROJECT_ROOT / ".env", override=False)


@lru_cache
def _load_json(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def channel_config() -> dict[str, Any]:
    return _load_json("channel.json")


def voice_config() -> dict[str, Any]:
    return _load_json("voice.json")


def style_config() -> dict[str, Any]:
    return _load_json("style.json")


def topic_queue() -> dict[str, Any]:
    return _load_json("topic-queue.json")


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def output_dir(test: bool = False) -> Path:
    base = OUTPUT_DIR / ("test" if test else "production")
    base.mkdir(parents=True, exist_ok=True)
    return base
