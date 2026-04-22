"""ピュア Python の動画アセンブラ。

Pillow で各シーンの静止画を作り、ffmpeg で結合・音声多重化して MP4 を作る。

シーン画像 = [背景] + [吹き出し + テキスト] + [ぷんぷんキャラ右下]

将来的に Remotion (React) でアニメーション付きにアップグレード予定。
このアセンブラは静止画でも十分視聴可能なベースラインを提供する。
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.config import ASSETS_DIR, style_config
from src.models import VideoScript


# ---------- フォント解決 ------------------------------------------------

def _find_font(size: int) -> ImageFont.FreeTypeFont:
    """日本語フォントを順番に探す。"""
    candidates = [
        ASSETS_DIR / "fonts" / "azuki.ttf",
        ASSETS_DIR / "fonts" / "PunpunFont.ttf",
        Path("/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for p in candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except OSError:
                continue
    return ImageFont.load_default()


# ---------- ぷんぷんキャラ ----------------------------------------------
# 互換用: 古い呼び出しをリダイレクト

def _make_punpun_placeholder(size: tuple[int, int]) -> Image.Image:
    """(互換) キャラ画像取得。新しい実装は src/video/character.py。"""
    from src.video.character import get_punpun
    return get_punpun(size=size, mouth="closed")


# ---------- 吹き出し ----------------------------------------------------

def _wrap_text(text: str, width: int) -> list[str]:
    """日本語想定の素朴な折り返し: width 字ごと改行 (句読点で優先的に折り返す)。"""
    if not text:
        return [""]
    lines: list[str] = []
    current = ""
    for ch in text:
        current += ch
        # 句読点で改行優先
        if ch in "。！？" and len(current) >= width // 2:
            lines.append(current)
            current = ""
        elif len(current) >= width and ch in "、":
            lines.append(current)
            current = ""
        elif len(current) >= width + 2:
            # 強制改行 (どこでも切る)
            lines.append(current)
            current = ""
    if current:
        lines.append(current)
    return lines


def _draw_speech_bubble(
    canvas: Image.Image,
    text: str,
    *,
    font: ImageFont.FreeTypeFont,
    width: int = 1400,
    pad: int = 40,
    max_lines: int = 3,
) -> None:
    """吹き出しを左下に描画 (背景画像の上に重ねる)。"""
    if not text:
        return
    # 各行の実測幅を見ながら、(width - pad*2) に収まる最大文字数を求める
    # safety margin を 1 文字分取って端ギリギリを避ける
    inner_w = width - pad * 2 - int(font.size * 1.0)
    chars_per_line = 8
    while chars_per_line < 60:
        sample = "あ" * (chars_per_line + 1)
        if int(font.getlength(sample)) > inner_w:
            break
        chars_per_line += 1
    lines = _wrap_text(text, chars_per_line)[:max_lines]

    # 行高さ
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 12

    # 実際のテキスト幅から bubble 幅を再計算
    text_w = max(int(font.getlength(line)) for line in lines) + pad * 2
    bubble_w = max(min(text_w, width), 400)
    bubble_h = line_h * len(lines) + pad * 2

    # 配置 (画面下部、左寄せ)
    x = 80
    y = canvas.height - bubble_h - 320

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # 影
    shadow_offset = 6
    od.rounded_rectangle(
        (x + shadow_offset, y + shadow_offset, x + bubble_w + shadow_offset, y + bubble_h + shadow_offset),
        radius=30, fill=(0, 0, 0, 60),
    )
    # 本体
    od.rounded_rectangle(
        (x, y, x + bubble_w, y + bubble_h),
        radius=30, fill=(255, 255, 255, 245), outline=(0, 0, 0, 255), width=4,
    )
    # しっぽ (右下に向けて) - 三角形
    tail = [
        (x + bubble_w - 60, y + bubble_h),
        (x + bubble_w + 30, y + bubble_h + 80),
        (x + bubble_w - 10, y + bubble_h - 5),
    ]
    od.polygon(tail, fill=(255, 255, 255, 245), outline=(0, 0, 0, 255))
    od.line([tail[0], tail[1]], fill=(0, 0, 0, 255), width=4)
    od.line([tail[1], tail[2]], fill=(0, 0, 0, 255), width=4)

    # テキスト
    text_y = y + pad
    for line in lines:
        od.text((x + pad, text_y), line, font=font, fill=(0, 0, 0, 255))
        text_y += line_h

    canvas.alpha_composite(overlay)


# ---------- シーン合成 ----------------------------------------------------

def _open_background(path: Path | None, size: tuple[int, int]) -> Image.Image:
    if path and path.exists():
        try:
            img = Image.open(path).convert("RGBA")
            # cover でリサイズ
            ratio_w = size[0] / img.width
            ratio_h = size[1] / img.height
            ratio = max(ratio_w, ratio_h)
            new = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
            # クロップ
            left = (new.width - size[0]) // 2
            top = (new.height - size[1]) // 2
            new = new.crop((left, top, left + size[0], top + size[1]))
            return new
        except Exception:
            pass
    bg = Image.new("RGBA", size, (245, 245, 240, 255))
    return bg


def render_scene_image(
    background_path: Path | None,
    text: str,
    out_path: Path,
    *,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    cfg = style_config()
    canvas = _open_background(background_path, (width, height))

    # ぷんぷん右下
    char_size = (cfg["character"]["size"]["width"], cfg["character"]["size"]["height"])
    punpun = _make_punpun_placeholder(char_size)
    cx = width - char_size[0] - cfg["character"]["offset"]["x"]
    cy = height - char_size[1] - cfg["character"]["offset"]["y"]
    canvas.alpha_composite(punpun, (cx, cy))

    # 吹き出し
    font = _find_font(cfg["speechBubble"]["fontSize"])
    _draw_speech_bubble(canvas, text, font=font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_path, "PNG")
    return out_path


# ---------- 動画組立 ----------------------------------------------------

def assemble_video(
    script: VideoScript,
    scene_images: list[Path],
    audio_path: Path,
    out_path: Path,
    *,
    fps: int = 30,
) -> Path:
    """シーン画像 + 音声 -> MP4。
    各シーンの長さは scene.duration_seconds から取得。
    """
    if len(scene_images) != len(script.scenes):
        raise ValueError("scene_images と script.scenes の長さが違います")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ffmpeg concat 用のファイルリスト
    with tempfile.TemporaryDirectory() as tmpd:
        list_file = Path(tmpd) / "scenes.txt"
        lines: list[str] = []
        for img, scene in zip(scene_images, script.scenes, strict=True):
            duration = scene.duration_seconds or 3.0
            lines.append(f"file '{img.resolve()}'")
            lines.append(f"duration {duration:.3f}")
        # concat demuxer のお作法: 最後の画像をもう一度
        lines.append(f"file '{scene_images[-1].resolve()}'")
        list_file.write_text("\n".join(lines), encoding="utf-8")

        # 1: 画像から無音動画
        silent = Path(tmpd) / "silent.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-fps_mode", "vfr",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264",
                "-vf", f"fps={fps}",
                "-preset", "medium",
                "-crf", "20",
                str(silent),
            ],
            check=True, capture_output=True,
        )

        # 2: 音声を多重化
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(silent),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(out_path),
            ],
            check=True, capture_output=True,
        )
    return out_path
