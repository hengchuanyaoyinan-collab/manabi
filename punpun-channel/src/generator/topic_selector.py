"""次に投稿する題材を選ぶ。

- queue が空でなければその先頭を返す
- 空ならアイデアバックログから優先度順 + シャッフルで補充
- 投稿後は posted に移し、queue から削除して保存
"""
from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

from src.config import CONFIG_DIR


QUEUE_PATH = CONFIG_DIR / "topic-queue.json"


def _load() -> dict:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    QUEUE_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def peek_next() -> dict | None:
    data = _load()
    queue = data.get("queue", [])
    if not queue:
        return None
    return queue[0]


def pop_next() -> dict | None:
    data = _load()
    queue = data.get("queue", [])
    if not queue:
        # backlog から補充
        backlog = data.get("ideasBacklog", [])
        if backlog:
            random.shuffle(backlog)
            new_topic = {
                "topic": backlog.pop(0),
                "category": "海外人物",
                "priority": "B",
                "note": "auto-promoted from backlog",
            }
            data["ideasBacklog"] = backlog
            data.setdefault("queue", []).append(new_topic)
            _save(data)
            queue = data["queue"]
        else:
            return None

    next_item = queue.pop(0)
    data["queue"] = queue
    _save(data)
    return next_item


def mark_posted(topic: str, video_id: str | None = None, views: int = 0) -> None:
    data = _load()
    posted = data.setdefault("posted", [])
    posted.append({
        "topic": topic,
        "videoId": video_id,
        "publishedAt": date.today().isoformat(),
        "views": views,
    })
    _save(data)


def already_posted(topic: str) -> bool:
    data = _load()
    return any(p.get("topic") == topic for p in data.get("posted", []))
