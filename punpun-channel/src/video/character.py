"""ぷんぷんキャラのレンダリング (v3 - 6 感情 + 口パク)。

感情:
- normal: 普通 (薄く口閉じ)
- shock: 驚き (目が大きく、口が開き、眉上がる)
- angry: 怒り (眉がつり上がる、口がへの字)
- laugh: 笑う (目が三日月、口が大きく U 字)
- sad: 悲しい (目の下がる、眉がハの字、口が下がる)
- think: 考える (目が細い、片眉上がる、口すぼめ)

口パクは音量 (mouth) と組み合わせる:
  render(emotion="shock", mouth="open") → 驚きの口開け
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

from src.config import ASSETS_DIR


MOUTH_CLOSED = "closed"
MOUTH_HALF = "half"
MOUTH_OPEN = "open"

EMOTIONS = ("normal", "shock", "angry", "laugh", "sad", "think")


def _draw_eye(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, emotion: str, side: str = "L"):
    """片目を描く。emotion に応じて形が変わる。"""
    if emotion == "laugh":
        # 三日月 (^) 形
        draw.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill="black", width=max(3, r // 3))
    elif emotion == "sad":
        # 下向きの半円 (下瞼が少し下がる)
        draw.ellipse((cx - r, cy - int(r * 0.7), cx + r, cy + int(r * 0.7)), fill="black")
    elif emotion == "think":
        # 細い目 (ほぼ線)
        draw.line((cx - r, cy, cx + r, cy), fill="black", width=max(3, r // 2))
    elif emotion == "shock":
        # 大きめの丸 (白目に黒点)
        draw.ellipse((cx - int(r * 1.2), cy - int(r * 1.2), cx + int(r * 1.2), cy + int(r * 1.2)),
                     fill="white", outline="black", width=2)
        draw.ellipse((cx - int(r * 0.6), cy - int(r * 0.6), cx + int(r * 0.6), cy + int(r * 0.6)),
                     fill="black")
    else:
        # 通常の丸
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="black")


def _draw_eyebrow(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, emotion: str, side: str):
    """片方の眉。"""
    brow_w = int(r * 1.2)
    brow_h = 14
    if emotion == "angry":
        # つり上がり (外側が上)
        if side == "L":
            # 左眉: 右下から左上へ
            draw.line((cx + brow_w // 2, cy + brow_h // 2, cx - brow_w // 2, cy - brow_h),
                      fill="black", width=5)
        else:
            draw.line((cx - brow_w // 2, cy + brow_h // 2, cx + brow_w // 2, cy - brow_h),
                      fill="black", width=5)
    elif emotion == "sad":
        # ハの字 (内側が上)
        if side == "L":
            draw.line((cx - brow_w // 2, cy + brow_h // 2, cx + brow_w // 2, cy - brow_h // 2),
                      fill="black", width=4)
        else:
            draw.line((cx + brow_w // 2, cy + brow_h // 2, cx - brow_w // 2, cy - brow_h // 2),
                      fill="black", width=4)
    elif emotion == "think":
        # 片方だけ上がる (左だけ上げる)
        if side == "L":
            draw.arc((cx - brow_w, cy - brow_h - 8, cx + brow_w, cy + brow_h - 8), 200, 340,
                     fill="black", width=4)
        else:
            draw.arc((cx - brow_w, cy - brow_h, cx + brow_w, cy + brow_h), 200, 340,
                     fill="black", width=4)
    elif emotion == "shock":
        # 驚き (高めの逆カーブ)
        draw.arc((cx - brow_w, cy - brow_h - 10, cx + brow_w, cy + brow_h - 10), 200, 340,
                 fill="black", width=5)
    else:
        # normal / laugh: 普通のアーチ
        draw.arc((cx - brow_w, cy - brow_h, cx + brow_w, cy + brow_h), 200, 340,
                 fill="black", width=4)


def _draw_mouth(
    draw: ImageDraw.ImageDraw,
    cx: int, cy: int, r: int,
    mouth: str, emotion: str,
):
    """口を描く。emotion + mouth の組み合わせ。"""
    # サイズ
    if mouth == MOUTH_CLOSED:
        lw, lh = int(r * 0.75), int(r * 0.4)
    elif mouth == MOUTH_HALF:
        lw, lh = int(r * 0.80), int(r * 0.55)
    else:
        lw, lh = int(r * 0.85), int(r * 0.75)

    if emotion == "angry":
        # への字 (逆 U): 上半分の弧
        draw.arc((cx - lw, cy - lh, cx + lw, cy + lh), 180, 360, fill=(200, 40, 40), width=6)
    elif emotion == "sad":
        # 下向き弧 (への字): 上半分の弧
        draw.arc((cx - lw, cy - lh, cx + lw, cy + lh // 2), 180, 360, fill=(200, 40, 40), width=5)
    elif emotion == "laugh":
        # 大きな U
        draw.chord((cx - lw, cy - lh, cx + lw, cy + lh), 0, 180, fill=(220, 50, 50),
                   outline=(120, 20, 20), width=3)
    elif emotion == "think":
        # 小さく右にずらす
        draw.ellipse((cx + lw // 3 - lw // 3, cy - lh // 3, cx + lw // 3 + lw // 3, cy + lh // 3),
                     fill=(220, 50, 50), outline=(120, 20, 20), width=2)
    else:
        # normal / shock: 普通の楕円
        draw.ellipse((cx - lw // 2, cy - lh // 2, cx + lw // 2, cy + lh // 2),
                     fill=(220, 50, 50), outline=(120, 20, 20), width=3)


def _draw_punpun(
    size: tuple[int, int] = (280, 280),
    mouth: str = MOUTH_CLOSED,
    emotion: str = "normal",
    angle: float = -8.0,
) -> Image.Image:
    """ぷんぷんを描画。"""
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2
    r = int(min(w, h) * 0.42)

    # 白い顔
    draw.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill="white",
        outline=(0, 0, 0, 255),
        width=5,
    )

    # 眉
    brow_y = cy - int(r * 0.55)
    _draw_eyebrow(draw, cx - int(r * 0.45), brow_y, r // 4, emotion, "L")
    _draw_eyebrow(draw, cx + int(r * 0.45), brow_y, r // 4, emotion, "R")

    # 目
    eye_r = max(8, r // 9)
    eye_y = cy - int(r * 0.18)
    _draw_eye(draw, cx - int(r * 0.45), eye_y, eye_r, emotion, "L")
    _draw_eye(draw, cx + int(r * 0.45), eye_y, eye_r, emotion, "R")

    # 涙 (sad のみ)
    if emotion == "sad":
        tear_x = cx + int(r * 0.55)
        tear_y = eye_y + eye_r
        draw.polygon(
            [(tear_x, tear_y), (tear_x - 6, tear_y + 14), (tear_x + 6, tear_y + 14)],
            fill=(100, 180, 230),
            outline=(60, 130, 200),
        )

    # 怒りマーク (angry のみ)
    if emotion == "angry":
        mark_x = cx + int(r * 0.9)
        mark_y = cy - int(r * 0.85)
        mark_r = 14
        # ギザギザ (4 本線)
        for a in (0, 90, 180, 270):
            rad = a * math.pi / 180
            x2 = mark_x + int(math.cos(rad) * mark_r)
            y2 = mark_y + int(math.sin(rad) * mark_r)
            draw.line((mark_x, mark_y, x2, y2), fill=(220, 50, 50), width=4)

    # 考え中マーク (think のみ)
    if emotion == "think":
        # ?マーク右上
        q_x = cx + int(r * 0.9)
        q_y = cy - int(r * 0.85)
        from PIL import ImageFont
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except Exception:
            f = ImageFont.load_default()
        draw.text((q_x - 10, q_y - 20), "?", font=f, fill=(50, 100, 200))

    # 汗 (shock のみ)
    if emotion == "shock":
        sweat_x = cx + int(r * 0.75)
        sweat_y = cy - int(r * 0.35)
        draw.polygon(
            [(sweat_x, sweat_y), (sweat_x - 8, sweat_y + 20), (sweat_x + 8, sweat_y + 20)],
            fill=(100, 200, 240),
            outline=(60, 150, 210),
        )

    # 口
    lip_cy = cy + int(r * 0.38)
    _draw_mouth(draw, cx, lip_cy, r, mouth, emotion)

    return img.rotate(angle, resample=Image.BICUBIC, expand=False)


@lru_cache(maxsize=64)
def get_punpun(
    size: tuple[int, int] = (280, 280),
    mouth: str = MOUTH_CLOSED,
    emotion: str = "normal",
) -> Image.Image:
    """ぷんぷん画像を取得 (感情 x 口 の組み合わせでキャッシュ)。"""
    emotion = emotion if emotion in EMOTIONS else "normal"
    # ユーザー提供があれば優先 (normal+closed のみ)
    if emotion == "normal" and mouth == MOUTH_CLOSED:
        real = ASSETS_DIR / "characters" / "punpun.png"
        if real.exists():
            try:
                return Image.open(real).convert("RGBA").resize(size, Image.LANCZOS)
            except Exception:
                pass
    return _draw_punpun(size=size, mouth=mouth, emotion=emotion)


def get_mouth_frame_for_audio(
    audio_amplitude: float,
    *,
    thresholds: tuple[float, float] = (0.05, 0.25),
) -> str:
    if audio_amplitude < thresholds[0]:
        return MOUTH_CLOSED
    if audio_amplitude < thresholds[1]:
        return MOUTH_HALF
    return MOUTH_OPEN


if __name__ == "__main__":
    for e in EMOTIONS:
        for m in (MOUTH_CLOSED, MOUTH_OPEN):
            img = get_punpun(mouth=m, emotion=e)
            img.save(f"/tmp/punpun_{e}_{m}.png")
            print(f"/tmp/punpun_{e}_{m}.png")
