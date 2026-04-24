"""競合チャンネル分析パイプライン。

1. YouTube Data API で競合チャンネルの動画を取得
2. 字幕を取得
3. Claude CLI で分析 (タイトルパターン・語彙・人気題材)
4. 結果を config/insights.json に保存
5. 発見した新題材を topic-queue.json に追加提案
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from src.analysis.youtube_client import YouTubeReadOnly, iso_duration_to_seconds
from src.config import CONFIG_DIR, PROJECT_ROOT

INSIGHTS_PATH = CONFIG_DIR / "insights.json"
ANALYSIS_PROMPT_TEMPLATE = """\
あなたは YouTube チャンネル運営の分析家です。以下のデータを読んで、
「ぷんぷんの世事見聞録」が学ぶべきパターンを抽出してください。

## 対象チャンネル
{channel_info}

## 最新動画 {n_videos} 本のメタデータ
{videos_json}

## 代表的な動画の文字起こし (上位 3 本)
{transcripts}

## 出力してほしいこと (JSON で)

```json
{{
  "channel_summary": "<1 文でこのチャンネルの特徴>",
  "title_patterns": [
    "<タイトルの法則・構文パターン>",
    "..."
  ],
  "vocabulary_trends": [
    "<頻出する語彙・フレーズ>",
    "..."
  ],
  "pacing": "<1 動画の平均尺、セリフのテンポ等>",
  "high_view_topics": ["<再生数上位の題材>", "..."],
  "low_view_topics": ["<再生伸びなかった題材>", "..."],
  "opportunity_topics": [
    "<ぷんぷんが取り上げるべき新題材>",
    "..."
  ],
  "hooks_and_techniques": [
    "<冒頭の掴み・演出テクニックの具体例>",
    "..."
  ],
  "risks": ["<避けるべき題材・表現>", "..."],
  "actionable_advice": [
    "<ぷんぷんの script-prompt.md に追加すべき指示>",
    "..."
  ]
}}
```

JSON のみを返してください。説明不要。
"""


def _call_claude_for_analysis(prompt: str) -> dict:
    """claude CLI で分析を実行し JSON を返す。"""
    import shutil
    cli = shutil.which("claude")
    if not cli:
        raise RuntimeError("claude CLI が見つかりません")
    proc = subprocess.run(
        [
            cli, "-p", prompt,
            "--model", "claude-haiku-4-5-20251001",
            "--output-format", "text",
            "--disallowedTools",
                "Bash,Read,Write,Edit,Grep,Glob,WebSearch,WebFetch,Task,TodoWrite,NotebookEdit",
        ],
        check=True, capture_output=True, text=True, timeout=600,
        stdin=subprocess.DEVNULL,
    )
    text = proc.stdout.strip()
    # ```json ``` を剥がす
    if text.startswith("```"):
        text = text[text.find("\n") + 1 :]
        if text.endswith("```"):
            text = text[: -3]
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"JSON not found in output: {text[:500]}")


def analyze_channel(
    channel_query: str,
    max_videos: int = 30,
    transcripts_top: int = 3,
    save: bool = True,
) -> dict:
    """チャンネル名で検索して 1 位のチャンネルを分析。"""
    yt = YouTubeReadOnly()
    channels = yt.search_channel(channel_query, max_results=3)
    if not channels:
        raise RuntimeError(f"チャンネルが見つかりません: {channel_query}")
    target = channels[0]
    ch_id = target["channelId"]

    print(f"📺 分析対象: {target['title']} ({ch_id})")
    ch = yt.get_channel(ch_id)
    print(f"   登録者: {ch['subscribers']:,}, 動画: {ch['videoCount']}")

    videos = yt.get_channel_videos(ch_id, max_results=max_videos)
    for v in videos:
        v["durationSeconds"] = iso_duration_to_seconds(v.get("duration") or "")
    print(f"   動画取得: {len(videos)} 本")

    # 再生数順にソートして上位の字幕を取る
    videos_by_views = sorted(videos, key=lambda x: x["views"], reverse=True)
    transcripts_data = []
    for v in videos_by_views[:transcripts_top]:
        print(f"   字幕取得: {v['title'][:40]}")
        tr = yt.get_transcript(v["videoId"])
        transcripts_data.append({
            "title": v["title"],
            "views": v["views"],
            "transcript": tr[:3000] if tr else "(字幕なし)",
        })

    # Claude に渡すためのコンパクトな形に
    compact_videos = [
        {
            "title": v["title"],
            "views": v["views"],
            "likes": v["likes"],
            "comments": v["comments"],
            "durationSec": v["durationSeconds"],
            "publishedAt": v["publishedAt"],
            "tags": v["tags"][:10],
        }
        for v in videos
    ]

    channel_info = (
        f"チャンネル名: {ch['title']}\n"
        f"登録者: {ch['subscribers']:,}\n"
        f"動画数: {ch['videoCount']}\n"
        f"累計視聴: {ch['viewCount']:,}\n"
        f"説明: {ch['description'][:300]}"
    )
    transcripts_str = "\n\n---\n\n".join(
        f"[{t['title']}] 再生数 {t['views']:,}\n{t['transcript'][:2000]}"
        for t in transcripts_data
    )
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        channel_info=channel_info,
        n_videos=len(videos),
        videos_json=json.dumps(compact_videos, ensure_ascii=False, indent=2)[:8000],
        transcripts=transcripts_str[:10000],
    )

    print("🤖 Claude で分析中 (数分かかります)...")
    insights = _call_claude_for_analysis(prompt)

    result = {
        "channelId": ch_id,
        "channelTitle": ch["title"],
        "analyzedAt": datetime.now().isoformat(),
        "videosCount": len(videos),
        "insights": insights,
        "top3Videos": [
            {"title": v["title"], "views": v["views"]}
            for v in videos_by_views[:3]
        ],
    }

    if save:
        _append_insights(result)
        print(f"✅ 保存: {INSIGHTS_PATH}")

    return result


def _append_insights(new_result: dict) -> None:
    """insights.json に追記。"""
    INSIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if INSIGHTS_PATH.exists():
        data = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8"))
    else:
        data = {"analyses": []}
    data["analyses"].append(new_result)
    data["lastUpdated"] = datetime.now().isoformat()
    INSIGHTS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def suggest_new_topics(insights: dict) -> list[str]:
    """分析結果から新題材候補を抽出。"""
    return insights.get("insights", {}).get("opportunity_topics", [])
