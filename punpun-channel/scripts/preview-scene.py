"""シーン画像プレビュー (動画にせず PNG だけ作る)。

スタイル調整で動画書き出しを毎回待つのは時間の無駄。
このスクリプトは指定セリフ + 背景タイプで画像 1 枚だけ作って、
スタイル調整を高速反復できる。

使い方:
    python3 scripts/preview-scene.py "テストのセリフ" --bg blank
    python3 scripts/preview-scene.py "ハンガリーの貴族" --bg map_world --highlight ハンガリー
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import BackgroundType, ImageHint
from src.video.assembler import render_scene_image
from src.video.image_fetcher import fetch_for_hint


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("text", help="ぷんぷんが喋るセリフ")
    p.add_argument(
        "--bg",
        choices=[t.value for t in BackgroundType],
        default="blank",
        help="背景タイプ",
    )
    p.add_argument("--keyword", default="", help="検索キーワード (portrait, illustration 等)")
    p.add_argument("--highlight", help="強調 (map 用)")
    p.add_argument("--out", default="output/preview.png")
    args = p.parse_args()

    hint = ImageHint(
        type=BackgroundType(args.bg),
        keyword=args.keyword or args.text[:20],
        highlight=args.highlight,
    )
    bg = fetch_for_hint(hint)
    out = render_scene_image(bg, args.text, Path(args.out))
    print(f"✅ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
