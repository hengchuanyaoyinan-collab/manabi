"""共通の型定義。
台本→動画パイプライン全体で使うデータモデルを Pydantic で定義する。
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class BackgroundType(str, Enum):
    """シーン背景の種類。これに応じて画像取得方法が変わる。"""

    PORTRAIT = "portrait"        # 肖像画 (Wikipedia Commons)
    MAP_WORLD = "map_world"      # 世界地図 (白地図 + 色塗り)
    MAP_REGION = "map_region"    # 地域地図
    MAP_HISTORICAL = "map_historical"  # 歴史地図 (例: 13世紀の世界)
    ILLUSTRATION = "illustration"  # いらすとや
    PHOTO = "photo"              # 写真 (Wikimedia)
    BLANK = "blank"              # 単色背景 (まとめ等)


class ImageHint(BaseModel):
    """シーンの背景を作るためのヒント。台本生成 AI が出力する。"""

    type: BackgroundType
    keyword: str = Field(..., description="検索キーワード")
    highlight: str | None = Field(None, description="強調したい地域・人物 (地図の場合)")
    overlay_keyword: str | None = Field(None, description="背景の上に重ねる小画像")
    annotation: str | None = Field(None, description="赤丸などの強調")


class Scene(BaseModel):
    """1 シーン = 1 セリフ。動画の最小単位。"""

    index: int
    chapter: int = Field(..., description="所属する章番号 (0=OP, 1-4=本編, 5=まとめ)")
    chapter_title: str = ""
    text: str = Field(..., description="ぷんぷんが喋るセリフ")
    image_hint: ImageHint
    duration_seconds: float | None = Field(
        None, description="音声合成後に確定する。null のうちは未確定"
    )
    audio_path: str | None = Field(None, description="生成された音声ファイル")


class Chapter(BaseModel):
    """章。OP/本編/まとめ。"""

    index: int
    title: str
    summary: str = ""


class VideoScript(BaseModel):
    """1 動画分の台本データ。"""

    topic: str
    title: str = Field(..., description="YouTube タイトル")
    description: str = Field(..., description="YouTube 概要欄")
    tags: list[str] = Field(default_factory=list)
    chapters: list[Chapter] = Field(default_factory=list)
    scenes: list[Scene] = Field(default_factory=list)
    thumbnail_text: str = Field(..., description="サムネのキャッチコピー")
    estimated_duration_seconds: float = 0.0

    def total_duration(self) -> float:
        """音声合成後の実測値を返す。"""
        return sum((s.duration_seconds or 0.0) for s in self.scenes)


class GenerationRequest(BaseModel):
    """動画生成のリクエスト。"""

    topic: str
    test_mode: bool = True
    publish: bool = False
    publish_at: str | None = None  # ISO8601


class TopicEntry(BaseModel):
    """題材キューの 1 エントリ。"""

    topic: str
    category: str = ""
    priority: Literal["A", "B", "C"] = "B"
    note: str = ""
    scheduled: str | None = None
