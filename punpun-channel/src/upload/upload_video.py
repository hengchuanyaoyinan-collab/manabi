"""YouTube アップロード。

resumable upload で動画を投稿し、サムネを設定。

env:
- TEST_MODE=true なら API 呼ばず log のみ
- privacyStatus=public/private/unlisted
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.config import CONFIG_DIR, channel_config, env
from src.models import VideoScript
from src.upload.youtube_oauth import get_credentials


def upload_to_youtube(
    script: VideoScript,
    video_path: Path,
    thumbnail_path: Path | None = None,
    *,
    publish_at_iso: str | None = None,
    test_mode: bool | None = None,
) -> str | None:
    """動画をアップロード。video id を返す。テストモードなら None。"""
    if test_mode is None:
        test_mode = env("TEST_MODE", "true").lower() == "true"

    cfg = channel_config()
    upload_cfg = cfg.get("upload", {})
    body = {
        "snippet": {
            "title": script.title[:100],
            "description": script.description[:5000],
            "tags": script.tags[:30],
            "categoryId": upload_cfg.get("category", "27"),
            "defaultLanguage": "ja",
            "defaultAudioLanguage": "ja",
        },
        "status": {
            "privacyStatus": upload_cfg.get("privacyStatus", "private"),
            "madeForKids": upload_cfg.get("madeForKids", False),
            "selfDeclaredMadeForKids": upload_cfg.get("madeForKids", False),
        },
    }
    if publish_at_iso:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at_iso

    if test_mode:
        print("🟡 TEST_MODE: 実アップロードはしません")
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return None

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        raise RuntimeError("google-api-python-client が未インストール")

    creds = get_credentials()
    if not creds:
        raise RuntimeError(
            "YouTube credentials が無い。`python3 src/upload/youtube_oauth.py` を先に実行"
        )

    youtube = build("youtube", "v3", credentials=creds)

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"  Uploading... {int(status.progress() * 100)}%")
    video_id = response["id"]
    print(f"✅ Video uploaded: https://www.youtube.com/watch?v={video_id}")

    # サムネ設定
    if thumbnail_path and thumbnail_path.exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
            ).execute()
            print("✅ Thumbnail set")
        except Exception as e:
            print(f"⚠️ Thumbnail set failed: {e}")

    return video_id


if __name__ == "__main__":
    print("This module is invoked from src/orchestrator.py.")
