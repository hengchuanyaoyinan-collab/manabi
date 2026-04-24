"""台本バッチ生成。

config/topic-queue.json の先頭 N 件を取得し、
test_data/<slug>.json として順次生成する。

これで「今週分」「今月分」の台本をまとめて作って
朝イチで動画レンダリングに回せる。

使い方:
    # キュー先頭 5 本の台本を生成
    python scripts/generate-script-batch.py --count 5

    # 特定題材を指定
    python scripts/generate-script-batch.py --topics "エリザベート・バートリ" "カリグラ帝" "則天武后"

    # 既存ファイルを上書き
    python scripts/generate-script-batch.py --count 5 --force
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CONFIG_DIR, PROJECT_ROOT
from src.generator.script_generator import generate_script


TEST_DATA = PROJECT_ROOT / "test_data"


def _slugify(text: str) -> str:
    """トピック名をファイル名に安全な ASCII slug にする。"""
    ascii_only = re.sub(r"[^\w]+", "_", text).strip("_").lower()
    if ascii_only and all(ord(c) < 128 for c in ascii_only):
        return ascii_only
    # 日本語のまま使う (ファイルシステムが Unicode 対応である前提)
    return re.sub(r"[\s/\\:*?\"<>|]+", "_", text).strip("_")


def _queued_topics() -> list[str]:
    qp = CONFIG_DIR / "topic-queue.json"
    if not qp.exists():
        return []
    data = json.loads(qp.read_text(encoding="utf-8"))
    return [item["topic"] for item in data.get("queue", [])]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--topics", nargs="*", help="指定トピック (空ならキューから)")
    p.add_argument("--count", type=int, default=5, help="キューから何本取るか")
    p.add_argument("--force", action="store_true", help="既存ファイルを上書き")
    p.add_argument("--model", default="claude-haiku-4-5-20251001")
    p.add_argument("--template", help="プロンプトテンプレート (templates/xxx.md)")
    p.add_argument("--out-dir", default="test_data", help="出力先ディレクトリ")
    p.add_argument("--queue", default="topic-queue.json",
                   help="題材キュー JSON (config/ 内)")
    args = p.parse_args()

    topics = args.topics or _queued_topics()[: args.count]
    if not topics:
        print("対象トピックが無い")
        return 1

    TEST_DATA.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    for i, topic in enumerate(topics, 1):
        slug = _slugify(topic)
        out_path = TEST_DATA / f"{slug}.json"

        if out_path.exists() and not args.force:
            print(f"[{i}/{len(topics)}] SKIP {topic} (既存: {out_path.name})")
            results.append({"topic": topic, "status": "skipped", "path": str(out_path)})
            continue

        print(f"[{i}/{len(topics)}] 生成中: {topic} → {out_path.name}")
        try:
            script = generate_script(topic, model=args.model, save_to=out_path)
            print(f"   ✅ {script.title} ({len(script.scenes)} scenes)")
            results.append({
                "topic": topic,
                "status": "ok",
                "path": str(out_path),
                "scenes": len(script.scenes),
                "title": script.title,
            })
        except Exception as e:
            print(f"   ❌ 失敗: {e}")
            results.append({"topic": topic, "status": "failed", "error": str(e)})

    print("\n=== サマリ ===")
    ok = sum(1 for r in results if r["status"] == "ok")
    skip = sum(1 for r in results if r["status"] == "skipped")
    fail = sum(1 for r in results if r["status"] == "failed")
    print(f"✅ 生成: {ok} / ⏭ スキップ: {skip} / ❌ 失敗: {fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
