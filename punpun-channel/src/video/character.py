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
    angle: float = 0.0,  # 過去動画は傾いてないので 0 に
) -> Image.Image:
    """ぷんぷんを描画 (過去動画の見た目を再現)。"""
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2
    # 顔は画像にぴったり (マージン少なめ)
    r = int(min(w, h) * 0.46)

    # 白い顔 (輪郭は太めだが過剰でない)
    draw.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill="white",
        outline=(0, 0, 0, 255),
        width=4,
    )

    # 眉 (高い位置、細く、緩やか)
    brow_y = cy - int(r * 0.48)
    _draw_eyebrow(draw, cx - int(r * 0.40), brow_y, r // 5, emotion, "L")
    _draw_eyebrow(draw, cx + int(r * 0.40), brow_y, r // 5, emotion, "R")

    # 目 (小さめ、中央寄り)
    eye_r = max(7, int(r * 0.10))
    eye_y = cy - int(r * 0.08)
    _draw_eye(draw, cx - int(r * 0.30), eye_y, eye_r, emotion, "L")
    _draw_eye(draw, cx + int(r * 0.30), eye_y, eye_r, emotion, "R")

    # 涙 (sad)
    if emotion == "sad":
        tear_x = cx + int(r * 0.42)
        tear_y = eye_y + eye_r
        draw.polygon(
            [(tear_x, tear_y), (tear_x - 6, tear_y + 14), (tear_x + 6, tear_y + 14)],
            fill=(100, 180, 230),
            outline=(60, 130, 200),
        )

    # 怒りマーク (angry)
    if emotion == "angry":
        mark_x = cx + int(r * 0.85)
        mark_y = cy - int(r * 0.75)
        mark_r = 14
        for a in (0, 90, 180, 270):
            rad = a * math.pi / 180
            x2 = mark_x + int(math.cos(rad) * mark_r)
            y2 = mark_y + int(math.sin(rad) * mark_r)
            draw.line((mark_x, mark_y, x2, y2), fill=(220, 50, 50), width=4)

    # ?マーク (think)
    if emotion == "think":
        q_x = cx + int(r * 0.85)
        q_y = cy - int(r * 0.75)
        from PIL import ImageFont
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except Exception:
            f = ImageFont.load_default()
        draw.text((q_x - 10, q_y - 20), "?", font=f, fill=(50, 100, 200))

    # 汗 (shock)
    if emotion == "shock":
        sweat_x = cx + int(r * 0.70)
        sweat_y = cy - int(r * 0.30)
        draw.polygon(
            [(sweat_x, sweat_y), (sweat_x - 8, sweat_y + 20), (sweat_x + 8, sweat_y + 20)],
            fill=(100, 200, 240),
            outline=(60, 150, 210),
        )

    # 口 (過去動画風: 大きめの赤い楕円)
    lip_cy = cy + int(r * 0.34)
    _draw_mouth_punpun(draw, cx, lip_cy, r, mouth, emotion)

    if angle != 0.0:
        return img.rotate(angle, resample=Image.BICUBIC, expand=False)
    return img


def _draw_mouth_punpun(
    draw: ImageDraw.ImageDraw,
    cx: int, cy: int, r: int,
    mouth: str, emotion: str,
):
    """過去動画風の口 (シンプルな赤い楕円)。emotion 別のバリエーション。"""
    if mouth == MOUTH_CLOSED:
        lw, lh = int(r * 0.42), int(r * 0.24)
    elif mouth == MOUTH_HALF:
        lw, lh = int(r * 0.46), int(r * 0.36)
    else:
        lw, lh = int(r * 0.50), int(r * 0.48)

    if emotion == "angry":
        # への字
        draw.arc((cx - lw, cy - lh, cx + lw, cy + lh), 180, 360, fill=(200, 40, 40), width=6)
    elif emotion == "sad":
        # 逆 U
        draw.arc((cx - lw, cy - lh * 2 // 3, cx + lw, cy + lh // 2), 180, 360, fill=(200, 40, 40), width=5)
    elif emotion == "laugh":
        # 大きな U (笑い)
        draw.chord((cx - lw, cy - lh, cx + lw, cy + lh), 0, 180, fill=(220, 50, 50),
                   outline=(150, 30, 30), width=3)
    elif emotion == "think":
        # 小さく
        small_lw = lw // 2
        small_lh = lh // 2
        draw.ellipse((cx - small_lw, cy - small_lh, cx + small_lw, cy + small_lh),
                     fill=(220, 50, 50), outline=(150, 30, 30), width=2)
    else:
        # 通常: 赤い楕円 (過去動画の特徴)
        draw.ellipse((cx - lw, cy - lh, cx + lw, cy + lh),
                     fill=(220, 50, 50), outline=(150, 30, 30), width=2)


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
