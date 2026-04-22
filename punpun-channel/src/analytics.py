"""動画パフォーマンス記録・分析。

毎日投稿される動画の成績 (再生数・維持率・登録者増加) を継続的に記録し、
ぷんぷんチャンネルの「何が伸びるか」のパターンを学習する。

データは config/analytics.json に保存。
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from src.config import CONFIG_DIR

ANALYTICS_PATH = CONFIG_DIR / "analytics.json"


def _load() -> dict:
    if not ANALYTICS_PATH.exists():
        return {"videos": [], "lastFetchedAt": None}
    return json.loads(ANALYTICS_PATH.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    ANALYTICS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def record_publish(
    video_id: str,
    *,
    topic: str,
    title: str,
    thumbnail_text: str,
    published_at: str | None = None,
    duration_seconds: float | None = None,
    tags: list[str] | None = None,
) -> None:
    """投稿時に呼ぶ。"""
    data = _load()
    entry = {
        "videoId": video_id,
        "topic": topic,
        "title": title,
        "thumbnailText": thumbnail_text,
        "publishedAt": published_at or datetime.now().isoformat(),
        "durationSeconds": duration_seconds,
        "tags": tags or [],
        "metrics": {
            "views": [],          # [{"at": iso, "value": n}, ...]
            "likes": [],
            "comments": [],
            "subscribers": [],    # 累計登録者
            "averageViewDurationSeconds": [],
        },
    }
    data["videos"].append(entry)
    _save(data)


def update_metrics(video_id: str, snapshot: dict) -> None:
    """YouTube API から取得した指標を追記。
    snapshot: {"views": int, "likes": int, "comments": int, "subscribers": int}
    """
    data = _load()
    now = datetime.now().isoformat()
    for v in data["videos"]:
        if v["videoId"] == video_id:
            for key in ("views", "likes", "comments", "subscribers", "averageViewDurationSeconds"):
                if key in snapshot:
                    v["metrics"].setdefault(key, []).append({"at": now, "value": snapshot[key]})
            data["lastFetchedAt"] = now
            _save(data)
            return


def best_topics(top_n: int = 10) -> list[dict]:
    """過去の伸びた題材ランキング (現在の最大再生数で評価)。"""
    data = _load()
    rows = []
    for v in data["videos"]:
        views = v["metrics"].get("views", [])
        peak = max((m["value"] for m in views), default=0)
        rows.append({"topic": v["topic"], "title": v["title"], "peakViews": peak})
    rows.sort(key=lambda r: r["peakViews"], reverse=True)
    return rows[:top_n]


def weekly_summary(start_date: date | None = None) -> dict:
    """直近 1 週間のまとめ。"""
    from datetime import timedelta
    if start_date is None:
        start_date = date.today() - timedelta(days=7)

    data = _load()
    week_videos = []
    for v in data["videos"]:
        try:
            pub = datetime.fromisoformat(v["publishedAt"].split("T")[0]).date()
        except Exception:
            continue
        if pub >= start_date:
            week_videos.append(v)

    total_views = sum(
        max((m["value"] for m in v["metrics"].get("views", [])), default=0)
        for v in week_videos
    )
    return {
        "weekStart": start_date.isoformat(),
        "videoCount": len(week_videos),
        "totalViews": total_views,
        "averageViews": total_views / max(len(week_videos), 1),
        "videos": [
            {
                "topic": v["topic"],
                "title": v["title"],
                "peakViews": max((m["value"] for m in v["metrics"].get("views", [])), default=0),
            }
            for v in week_videos
        ],
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "weekly":
        print(json.dumps(weekly_summary(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "best":
        print(json.dumps(best_topics(), ensure_ascii=False, indent=2))
    else:
        print("Usage: python3 src/analytics.py [weekly|best]")
