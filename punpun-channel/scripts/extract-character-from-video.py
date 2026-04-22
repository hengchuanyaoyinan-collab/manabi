"""過去動画 (.mp4) からぷんぷんキャラの画像を抽出する補助ツール。

ユーザーが Windows PC で過去のぷんぷん動画を持っていれば、それから
キャラ画像を切り出してプロジェクトに配置できる。

使い方:
    python3 scripts/extract-character-from-video.py <video.mp4> [--frame 30]

これで指定フレームの右下 (キャラ位置) の領域を切り抜いて
assets/characters/punpun_extracted.png に保存する。

切り抜いた画像を assets/characters/punpun.png にリネームすれば
パイプラインがそれを使うようになる (背景の白を透過するなどの
追加加工はユーザーが画像編集ソフトで行う想定)。
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def extract_frame(video: Path, frame_index: int = 30) -> Path:
    out = Path("/tmp/_frame.png") if sys.platform != "win32" else Path("./_frame.png")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video),
            "-vf", f"select='eq(n,{frame_index})'",
            "-frames:v", "1",
            str(out),
        ],
        check=True, capture_output=True,
    )
    return out


def crop_character_region(frame: Path, out: Path) -> Path:
    """フレームの右下からキャラ領域を切り抜く。
    YouTubeの過去動画フォーマット: 1920x1080 で右下に約 280x280。
    """
    from PIL import Image
    img = Image.open(frame)
    w, h = img.size
    # 右下から少し余白を取って切り抜く
    char_w, char_h = 320, 320
    margin = 20
    box = (w - char_w - margin, h - char_h - margin, w - margin, h - margin)
    crop = img.crop(box)
    crop.save(out)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("video", help="ぷんぷん過去動画 (.mp4)")
    p.add_argument("--frame", type=int, default=30, help="切り抜くフレーム番号")
    p.add_argument(
        "--out",
        default="assets/characters/punpun_extracted.png",
        help="出力先",
    )
    args = p.parse_args()

    video = Path(args.video)
    if not video.exists():
        print(f"❌ {video} が見つかりません", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"フレーム {args.frame} を抽出中...")
    frame = extract_frame(video, args.frame)
    print(f"キャラ領域を切り抜き中...")
    crop_character_region(frame, out)
    print(f"✅ {out}")
    print()
    print("次のステップ:")
    print("  1. 切り抜いた画像を確認")
    print("  2. 必要なら背景を透過 (画像編集ソフトで)")
    print(f"  3. {out} を assets/characters/punpun.png にリネーム")
    return 0


if __name__ == "__main__":
    sys.exit(main())
