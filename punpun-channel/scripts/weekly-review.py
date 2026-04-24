"""週次レビュー。毎週日曜 23:00 に起動。

処理:
1. 過去 7 日の投稿動画の成績を集計
2. Claude CLI で勝ちパターン/負けパターン分析
3. 結果を config/weekly-reviews.json に保存
4. Discord に要点通知

出力:
- config/weekly-reviews.json (累積)
- Discord 通知
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analytics import weekly_summary, best_topics
from src.config import CONFIG_DIR
from src.notify.discord import send, COLOR_INFO


REVIEWS_PATH = CONFIG_DIR / "weekly-reviews.json"


ANALYSIS_PROMPT = """\
以下は先週の投稿データです。成功・失敗のパターンを抽出してください。

## 週次サマリー
{summary}

## 全期間ランキング (再生数上位)
{best}

## 次週への改善提案を JSON で出力してください。マークダウン装飾なしで生 JSON のみ。

```json
{{
  "week_summary": "<1 文で今週の総括>",
  "top_performers": ["<勝った動画の共通点>"],
  "underperformers": ["<負けた動画の共通点>"],
  "title_insights": ["<タイトルに関する気付き>"],
  "topic_insights": ["<題材選定に関する気付き>"],
  "next_week_focus": ["<来週特に注力すべきこと>"],
  "prompt_updates": [
    "<script-prompt.md に追記すべき具体的な指示>"
  ]
}}
```
"""


def _call_claude(prompt: str) -> dict:
    cli = shutil.which("claude")
    if not cli:
        raise RuntimeError("claude CLI なし")
    proc = subprocess.run(
        [cli, "-p", prompt,
         "--model", "claude-haiku-4-5-20251001",
         "--output-format", "text",
         "--disallowedTools",
         "Bash,Read,Write,Edit,Grep,Glob,WebSearch,WebFetch,Task,TodoWrite,NotebookEdit",
        ],
        check=True, capture_output=True, text=True, timeout=600,
        stdin=subprocess.DEVNULL,
    )
    text = proc.stdout.strip()
    if text.startswith("```"):
        text = text[text.find("\n") + 1 :]
        if text.endswith("```"):
            text = text[: -3]
    start = text.find("{")
    end = text.rfind("}")
    return json.loads(text[start : end + 1])


def _save_review(review: dict) -> None:
    REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if REVIEWS_PATH.exists():
        data = json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))
    else:
        data = {"reviews": []}
    data["reviews"].append(review)
    data["lastUpdated"] = datetime.now().isoformat()
    REVIEWS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--no-discord", action="store_true")
    p.add_argument("--no-claude", action="store_true",
                   help="Claude 呼ばずに集計のみ")
    args = p.parse_args()

    start_date = date.today() - timedelta(days=args.days)
    summary = weekly_summary(start_date=start_date)
    best = best_topics(top_n=10)

    print(f"\n=== 週次レビュー ({start_date.isoformat()} 以降) ===")
    print(f"投稿本数: {summary['videoCount']}")
    print(f"合計再生数: {summary['totalViews']:,}")
    print(f"平均再生数: {summary['averageViews']:,.0f}")

    if args.no_claude or summary["videoCount"] == 0:
        review = {
            "generatedAt": datetime.now().isoformat(),
            "startDate": start_date.isoformat(),
            "summary": summary,
            "bestAllTime": best,
        }
    else:
        print("🤖 Claude で分析中...")
        try:
            insights = _call_claude(
                ANALYSIS_PROMPT.format(
                    summary=json.dumps(summary, ensure_ascii=False, indent=2)[:4000],
                    best=json.dumps(best, ensure_ascii=False, indent=2)[:2000],
                )
            )
        except Exception as e:
            print(f"⚠️  Claude 分析失敗: {e}")
            insights = {}
        review = {
            "generatedAt": datetime.now().isoformat(),
            "startDate": start_date.isoformat(),
            "summary": summary,
            "bestAllTime": best,
            "insights": insights,
        }

    _save_review(review)
    print(f"✅ 保存: {REVIEWS_PATH}")

    if not args.no_discord:
        lines = [
            f"📊 **週次レビュー**",
            f"投稿: {summary['videoCount']} 本 / 再生: {summary['totalViews']:,}",
        ]
        insights = review.get("insights", {})
        if insights.get("week_summary"):
            lines.append(f"\n{insights['week_summary']}")
        if insights.get("next_week_focus"):
            lines.append("\n**来週の注力:**")
            for f in insights["next_week_focus"][:3]:
                lines.append(f"- {f}")
        send(
            description="\n".join(lines),
            title="ぷんぷん 週次レビュー",
            color=COLOR_INFO,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
