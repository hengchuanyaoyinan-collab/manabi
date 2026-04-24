"""日次アナリティクス取得。

毎朝 09:00 に起動:
- YouTube Analytics API から昨日投稿動画の成績を取得
- config/analytics.json に追記
- Discord に結果サマリー送信

必要な認証:
- youtube-token.json (投稿用 OAuth 認証済み) → 読み取りスコープ含む必要あり
  → src/upload/youtube_oauth.py で再認証時に analytics.readonly スコープ追加推奨

Google Cloud Console:
- YouTube Data API v3
- YouTube Analytics API v2 (両方有効化)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analytics import update_metrics
from src.notify.discord import notify_info, send, COLOR_INFO
from src.upload.youtube_oauth import get_credentials


def fetch_video_stats(video_ids: list[str]) -> dict[str, dict]:
    """YouTube Data API v3 で動画の再生数等を取得。"""
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError("google-api-python-client 未インストール")

    creds = get_credentials()
    if not creds:
        raise RuntimeError("OAuth 未認証。python3 src/upload/youtube_oauth.py を実行")

    yt = build("youtube", "v3", credentials=creds)
    out: dict[str, dict] = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i : i + 50]
        r = yt.videos().list(part="statistics", id=",".join(chunk)).execute()
        for item in r.get("items", []):
            s = item["statistics"]
            out[item["id"]] = {
                "views": int(s.get("viewCount", 0)),
                "likes": int(s.get("likeCount", 0)),
                "comments": int(s.get("commentCount", 0)),
            }
    return out


def fetch_analytics(video_ids: list[str], days: int = 7) -> dict[str, dict]:
    """YouTube Analytics API v2 で詳細指標を取得。
    - averageViewDuration (秒)
    - averageViewPercentage (%)
    - impressions (表示回数)
    - impressionClickThroughRate (CTR %)
    """
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError("google-api-python-client 未インストール")

    creds = get_credentials()
    if not creds:
        return {}

    analytics = build("youtubeAnalytics", "v2", credentials=creds)
    today = date.today()
    start = today - timedelta(days=days)

    out: dict[str, dict] = {}
    for vid in video_ids:
        try:
            r = analytics.reports().query(
                ids="channel==MINE",
                startDate=start.isoformat(),
                endDate=today.isoformat(),
                metrics="views,averageViewDuration,averageViewPercentage",
                dimensions="video",
                filters=f"video=={vid}",
            ).execute()
            rows = r.get("rows", [])
            if rows:
                row = rows[0]
                col = r.get("columnHeaders", [])
                names = [c["name"] for c in col]
                out[vid] = dict(zip(names, row[1:]))
        except Exception as e:
            print(f"⚠️  {vid} analytics failed: {e}")
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=1,
                   help="過去何日の動画を対象にするか (デフォ 1)")
    p.add_argument("--no-discord", action="store_true")
    args = p.parse_args()

    # analytics.json から登録済動画 id を読む
    analytics_path = Path(__file__).resolve().parent.parent / "config" / "analytics.json"
    if not analytics_path.exists():
        print("config/analytics.json が無い")
        return 1
    data = json.loads(analytics_path.read_text(encoding="utf-8"))

    # 最近 N 日以内に publish された動画を対象
    cutoff = date.today() - timedelta(days=args.days * 2)
    target = [v for v in data["videos"]
              if v.get("videoId")
              and v.get("publishedAt", "") >= cutoff.isoformat()]
    if not target:
        print("対象動画なし")
        return 0

    print(f"対象: {len(target)} 本")
    video_ids = [v["videoId"] for v in target]

    try:
        stats = fetch_video_stats(video_ids)
    except Exception as e:
        print(f"❌ stats 取得失敗: {e}")
        return 1

    # 記録
    summary_lines = []
    for v in target:
        vid = v["videoId"]
        if vid not in stats:
            continue
        update_metrics(vid, stats[vid])
        summary_lines.append(
            f"- {v['topic']}: {stats[vid]['views']:,} views, "
            f"{stats[vid]['likes']} likes"
        )

    print("\n".join(summary_lines))

    # Discord 通知
    if not args.no_discord and summary_lines:
        send(
            description="\n".join(summary_lines),
            title=f"📊 日次レポート ({date.today().isoformat()})",
            color=COLOR_INFO,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
