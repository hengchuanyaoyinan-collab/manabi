"""競合チャンネル分析 CLI。

使い方:
    # ぴよぴーよ速報を分析
    python3 scripts/analyze-competitors.py "ぴよぴーよ速報"

    # 複数まとめて
    python3 scripts/analyze-competitors.py "ぴよぴーよ速報" "大人の学び直しTV" "ホモサピのいい話"

    # 深く (動画 50 本 + 字幕 5 本)
    python3 scripts/analyze-competitors.py --deep "ぴよぴーよ速報"

出力:
    config/insights.json  — 全分析結果
    stdout              — サマリー

事前準備:
    1. https://console.cloud.google.com でプロジェクト作成、
       YouTube Data API v3 を有効化、API キー発行
    2. .env に YOUTUBE_API_KEY=AIza... を追加
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analysis.competitor_analyzer import analyze_channel


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("channels", nargs="+", help="分析するチャンネル名 (複数指定可)")
    p.add_argument("--deep", action="store_true",
                   help="深く分析 (50 本 + 上位 5 本字幕)")
    p.add_argument("--max-videos", type=int)
    p.add_argument("--transcripts-top", type=int)
    args = p.parse_args()

    max_videos = args.max_videos or (50 if args.deep else 30)
    transcripts_top = args.transcripts_top or (5 if args.deep else 3)

    for ch_query in args.channels:
        print(f"\n{'=' * 60}")
        print(f"▶ 分析: {ch_query}")
        print("=" * 60)
        try:
            result = analyze_channel(
                ch_query,
                max_videos=max_videos,
                transcripts_top=transcripts_top,
            )
            insights = result.get("insights", {})
            print(f"\n📊 サマリー: {insights.get('channel_summary', 'n/a')}")
            print(f"\n🏷 タイトルパターン:")
            for p in insights.get("title_patterns", [])[:5]:
                print(f"  - {p}")
            print(f"\n🎯 新題材チャンス:")
            for t in insights.get("opportunity_topics", [])[:5]:
                print(f"  - {t}")
            print(f"\n💡 script-prompt に追加すべき指示:")
            for a in insights.get("actionable_advice", [])[:5]:
                print(f"  - {a}")
        except Exception as e:
            print(f"❌ 失敗: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
