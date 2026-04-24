"""YouTube Data API v3 クライアント (読み取り専用)。

競合チャンネルの動画メタデータ取得専用。投稿用 OAuth とは別に
API キーだけで済む読み取り専用クライアント。

事前準備:
1. https://console.cloud.google.com でプロジェクト作成
2. YouTube Data API v3 を有効化
3. API キー発行 (認証情報 → 認証情報を作成 → API キー)
4. .env に `YOUTUBE_API_KEY=AIza...` を追加
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.config import env


class YouTubeReadOnly:
    """API キー認証の読み取り専用クライアント。"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or env("YOUTUBE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "YOUTUBE_API_KEY が設定されていません。.env に追加してください。"
            )
        try:
            from googleapiclient.discovery import build
        except ImportError:
            raise RuntimeError("google-api-python-client をインストールしてください")
        self.yt = build("youtube", "v3", developerKey=self.api_key)

    # --- チャンネル検索 / 取得 ---

    def search_channel(self, query: str, max_results: int = 5) -> list[dict]:
        """チャンネル名で検索。上位をリストで返す。"""
        r = self.yt.search().list(
            part="snippet", q=query, type="channel", maxResults=max_results,
        ).execute()
        return [
            {
                "channelId": item["snippet"]["channelId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
            }
            for item in r.get("items", [])
        ]

    def get_channel(self, channel_id: str) -> dict:
        """チャンネル詳細 (統計含む)。"""
        r = self.yt.channels().list(
            part="snippet,statistics,contentDetails", id=channel_id,
        ).execute()
        items = r.get("items", [])
        if not items:
            return {}
        it = items[0]
        return {
            "channelId": channel_id,
            "title": it["snippet"]["title"],
            "description": it["snippet"].get("description", ""),
            "subscribers": int(it["statistics"].get("subscriberCount", 0)),
            "videoCount": int(it["statistics"].get("videoCount", 0)),
            "viewCount": int(it["statistics"].get("viewCount", 0)),
            "uploadsPlaylistId": it["contentDetails"]["relatedPlaylists"]["uploads"],
        }

    # --- 動画一覧 / 詳細 ---

    def get_channel_videos(
        self, channel_id: str, max_results: int = 50
    ) -> list[dict]:
        """チャンネルの最新動画を取得。"""
        ch = self.get_channel(channel_id)
        uploads = ch.get("uploadsPlaylistId")
        if not uploads:
            return []
        video_ids: list[str] = []
        next_token = None
        while len(video_ids) < max_results:
            r = self.yt.playlistItems().list(
                part="contentDetails",
                playlistId=uploads,
                maxResults=min(50, max_results - len(video_ids)),
                pageToken=next_token,
            ).execute()
            for item in r.get("items", []):
                video_ids.append(item["contentDetails"]["videoId"])
            next_token = r.get("nextPageToken")
            if not next_token:
                break
        return self.get_video_details(video_ids)

    def get_video_details(self, video_ids: list[str]) -> list[dict]:
        """動画 ID リストから詳細 (統計・時間・タグ等) を取得。"""
        out: list[dict] = []
        # YouTube API は 50 個ずつ
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i : i + 50]
            r = self.yt.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(chunk),
            ).execute()
            for item in r.get("items", []):
                snip = item["snippet"]
                stats = item.get("statistics", {})
                content = item.get("contentDetails", {})
                out.append({
                    "videoId": item["id"],
                    "title": snip["title"],
                    "description": snip.get("description", ""),
                    "tags": snip.get("tags", []),
                    "publishedAt": snip.get("publishedAt"),
                    "duration": content.get("duration"),  # ISO 8601 ("PT12M34S")
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "thumbnailUrl": snip["thumbnails"]["high"]["url"],
                    "channelId": snip.get("channelId"),
                    "channelTitle": snip.get("channelTitle"),
                })
        return out

    # --- 字幕 ---

    def get_transcript(self, video_id: str, languages: list[str] | None = None) -> str:
        """字幕 (文字起こし) を取得。"""
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        try:
            api = YouTubeTranscriptApi()
            tlist = api.list(video_id)
            # 日本語 -> 英語 -> 自動生成の順で試す
            for lang in (languages or ["ja", "en"]):
                try:
                    t = tlist.find_transcript([lang])
                    return "\n".join(e.text for e in t.fetch())
                except Exception:
                    pass
            # フォールバック: 自動生成を手に入れる
            try:
                t = tlist.find_generated_transcript(["ja", "en"])
                return "\n".join(e.text for e in t.fetch())
            except Exception:
                return ""
        except Exception:
            return ""


# 便利関数 -----------------------------------------------------------

def iso_duration_to_seconds(iso: str) -> int:
    """PT1H23M45S 形式を秒に。"""
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


if __name__ == "__main__":
    import sys
    try:
        yt = YouTubeReadOnly()
    except RuntimeError as e:
        print(e)
        sys.exit(1)
    if len(sys.argv) > 1:
        results = yt.search_channel(sys.argv[1])
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("Usage: python3 -m src.analysis.youtube_client <channel name>")
