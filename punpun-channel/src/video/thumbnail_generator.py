"""サムネイル生成。

ぴよぴーよ・大人の学び直し系の勝ちパターンを参考に:
- 極太フォント
- 強い色 (赤・黒・黄)
- 煽りワード (8〜12 字)
- キャラクターを大きく配置
- 背景は人物肖像 or 印象的な画像

1280x720 PNG で出力 (YouTube サムネ標準サイズ)。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.config import ASSETS_DIR
from src.video.assembler import _find_font, _make_punpun_placeholder


THUMB_W = 1280
THUMB_H = 720


def _stroke_text(
    draw: ImageDraw.ImageDraw,
    pos: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int] = (255, 255, 255),
    stroke_fill: tuple[int, int, int] = (0, 0, 0),
    stroke_width: int = 8,
) -> None:
    draw.text(pos, text, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)


def generate_thumbnail(
    text: str,
    background_path: Path | None,
    out_path: Path,
    *,
    title_color: tuple[int, int, int] = (255, 230, 0),  # 黄色
    accent_color: tuple[int, int, int] = (220, 30, 30),  # 赤
    width: int = THUMB_W,
    height: int = THUMB_H,
) -> Path:
    """サムネ生成。
    text は煽り文 (例: "4000 万人を殺した男")。
    """
    canvas = Image.new("RGBA", (width, height), (20, 20, 20, 255))

    # 背景
    if background_path and background_path.exists():
        try:
            bg = Image.open(background_path).convert("RGBA")
            ratio = max(width / bg.width, height / bg.height)
            bg = bg.resize((int(bg.width * ratio), int(bg.height * ratio)), Image.LANCZOS)
            left = (bg.width - width) // 2
            top = (bg.height - height) // 2
            bg = bg.crop((left, top, left + width, top + height))
            # 暗くして文字が読みやすいように
            dark = Image.new("RGBA", (width, height), (0, 0, 0, 90))
            canvas.alpha_composite(bg)
            canvas.alpha_composite(dark)
        except Exception:
            pass

    draw = ImageDraw.Draw(canvas)

    # メインテキスト (極太、上部配置)
    if len(text) <= 6:
        font_size = 200
    elif len(text) <= 10:
        font_size = 150
    elif len(text) <= 14:
        font_size = 110
    else:
        font_size = 90
    font = _find_font(font_size)

    lines = _split_for_thumbnail(text)
    line_h = font.size + 20

    total_h = line_h * len(lines)
    start_y = (height - total_h) // 2

    for i, line in enumerate(lines):
        text_w = int(font.getlength(line))
        x = (width - text_w) // 2
        y = start_y + i * line_h
        # 行ごとに色を変える (1 行目=黄、2 行目=赤等)
        color = title_color if i == 0 else accent_color
        _stroke_text(draw, (x, y), line, font, fill=color, stroke_fill=(0, 0, 0), stroke_width=10)

    # ぷんぷんを右下に
    char_size = (240, 240)
    punpun = _make_punpun_placeholder(char_size)
    canvas.alpha_composite(punpun, (width - char_size[0] - 20, height - char_size[1] - 20))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path


def _split_for_thumbnail(text: str) -> list[str]:
    """サムネ用に 1〜2 行に分割。改行記号 / があれば優先。"""
    if "/" in text:
        return [s.strip() for s in text.split("/")][:2]
    if "\n" in text:
        return text.split("\n")[:2]
    if len(text) > 9:
        mid = len(text) // 2
        # 句読点で分けるのを優先
        for offset in range(0, 3):
            for i in (mid - offset, mid + offset):
                if 0 < i < len(text) and text[i] in "、。！？":
                    return [text[: i + 1], text[i + 1 :]]
        return [text[:mid], text[mid:]]
    return [text]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--text", default="4000 万人を殺した狂気")
    p.add_argument("--bg")
    p.add_argument("--out", default="output/thumbnail_test.png")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    bg = Path(args.bg) if args.bg else None
    out = generate_thumbnail(args.text, bg, Path(args.out))
    print(f"✅ {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
