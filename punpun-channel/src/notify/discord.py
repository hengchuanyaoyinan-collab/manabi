"""Discord webhook 通知。

環境変数:
    DISCORD_WEBHOOK_URL - Discord のチャンネルで「ウェブフック」→「新しいウェブフック」で発行

使い方:
    from src.notify.discord import notify_success, notify_error
    notify_success("✅ 動画公開", video_url="https://...", title="...")
    notify_error("台本生成失敗", detail="claude CLI timeout")
"""
from __future__ import annotations

import logging
from typing import Any

import requests

from src.config import env

logger = logging.getLogger(__name__)

COLOR_SUCCESS = 0x2ecc71  # 緑
COLOR_INFO = 0x3498db     # 青
COLOR_WARN = 0xf39c12     # 橙
COLOR_ERROR = 0xe74c3c    # 赤


def _webhook_url() -> str | None:
    return env("DISCORD_WEBHOOK_URL")


def send(
    description: str,
    *,
    title: str = "ぷんぷんの世事見聞録",
    color: int = COLOR_INFO,
    fields: list[dict[str, str]] | None = None,
    url: str | None = None,
    thumbnail_url: str | None = None,
) -> bool:
    """Discord に送る。成功 True / 失敗 False。"""
    webhook = _webhook_url()
    if not webhook:
        logger.info("DISCORD_WEBHOOK_URL 未設定のためスキップ")
        return False

    embed: dict[str, Any] = {
        "title": title,
        "description": description,
        "color": color,
    }
    if url:
        embed["url"] = url
    if fields:
        embed["fields"] = [
            {"name": f["name"], "value": f["value"], "inline": f.get("inline", False)}
            for f in fields
        ]
    if thumbnail_url:
        embed["thumbnail"] = {"url": thumbnail_url}

    try:
        r = requests.post(webhook, json={"embeds": [embed]}, timeout=5)
        r.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Discord 通知失敗: {e}")
        return False


def notify_success(
    message: str,
    *,
    video_url: str | None = None,
    title: str | None = None,
    thumbnail_url: str | None = None,
    duration_sec: float | None = None,
    scene_count: int | None = None,
) -> bool:
    """動画公開成功通知。"""
    fields = []
    if title:
        fields.append({"name": "タイトル", "value": title[:80]})
    if duration_sec:
        mins = int(duration_sec // 60)
        secs = int(duration_sec % 60)
        fields.append({"name": "長さ", "value": f"{mins}:{secs:02d}", "inline": True})
    if scene_count:
        fields.append({"name": "シーン数", "value": str(scene_count), "inline": True})

    return send(
        description=message,
        title="✅ 動画公開成功",
        color=COLOR_SUCCESS,
        fields=fields or None,
        url=video_url,
        thumbnail_url=thumbnail_url,
    )


def notify_error(
    stage: str,
    detail: str,
    *,
    topic: str | None = None,
) -> bool:
    """エラー通知。"""
    fields = [
        {"name": "Stage", "value": stage, "inline": True},
    ]
    if topic:
        fields.append({"name": "題材", "value": topic, "inline": True})
    fields.append({"name": "詳細", "value": detail[:500]})

    return send(
        description=f"❌ パイプラインが失敗しました",
        title="⚠️  ぷんぷん 自動投稿エラー",
        color=COLOR_ERROR,
        fields=fields,
    )


def notify_info(message: str, **kwargs: Any) -> bool:
    """一般通知。"""
    return send(message, color=COLOR_INFO, **kwargs)


def notify_report(
    stats: dict[str, Any],
) -> bool:
    """日次/週次レポート通知。"""
    fields = [
        {"name": k, "value": str(v), "inline": True}
        for k, v in stats.items()
    ]
    return send(
        description="先週のパフォーマンス",
        title="📊 ぷんぷん 週次レポート",
        color=COLOR_INFO,
        fields=fields,
    )


if __name__ == "__main__":
    # 簡易テスト
    import sys
    if not _webhook_url():
        print("DISCORD_WEBHOOK_URL が未設定。.env に追加してからテストしてください。")
        sys.exit(1)
    ok = notify_info("Discord 通知テスト (from punpun-channel)")
    print("Sent" if ok else "Failed")
