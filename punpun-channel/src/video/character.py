"""ぷんぷんキャラのレンダリング。

過去動画のスクショを参考に:
- 白丸顔 + 黒目 2 点 + 赤い唇 + 細眉
- 少し右に傾いて (斜めを向いている風)
- 口を 3 段階 (閉じ・半開・全開) で用意 → リップシンク可能
- assets/characters/punpun.png があればそれを使う (ユーザーが過去動画から抽出)
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from src.config import ASSETS_DIR


MOUTH_CLOSED = "closed"
MOUTH_HALF = "half"
MOUTH_OPEN = "open"


def _draw_punpun(
    size: tuple[int, int] = (280, 280),
    mouth: str = MOUTH_CLOSED,
    angle: float = -8.0,  # 右に少し傾ける
) -> Image.Image:
    """ぷんぷんを描画。mouth = closed/half/open。"""
    w, h = size
    # 最終サイズのまま描く。顔の直径は size の 70% にして、回転でも切れないようにマージンを取る。
    W, H = w, h
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    # 顔半径: 画像の最小辺の 42% (周囲にマージンを残す)
    r = int(min(W, H) * 0.42)

    # 白い顔
    draw.ellipse(
        (cx - r, cy - r, cx + r, cy + r),
        fill="white",
        outline=(0, 0, 0, 255),
        width=5,
    )

    # 細眉 (アーチ状)
    brow_y = cy - int(r * 0.55)
    brow_w = int(r * 0.32)
    brow_h = 18
    # 左眉
    draw.arc(
        (
            cx - int(r * 0.45) - brow_w,
            brow_y - brow_h,
            cx - int(r * 0.45) + brow_w,
            brow_y + brow_h,
        ),
        200, 340,
        fill="black",
        width=5,
    )
    # 右眉
    draw.arc(
        (
            cx + int(r * 0.45) - brow_w,
            brow_y - brow_h,
            cx + int(r * 0.45) + brow_w,
            brow_y + brow_h,
        ),
        200, 340,
        fill="black",
        width=5,
    )

    # 目 (黒点、大きめの丸)
    eye_r = max(8, r // 9)
    eye_y = cy - int(r * 0.18)
    for dx in (-1, 1):
        ex = cx + dx * int(r * 0.45)
        draw.ellipse(
            (ex - eye_r, eye_y - eye_r, ex + eye_r, eye_y + eye_r),
            fill="black",
        )

    # 口 (赤い楕円、mouth 状態で大きさが変わる)
    lip_cx = cx
    lip_cy = cy + int(r * 0.35)
    if mouth == MOUTH_CLOSED:
        lip_w = int(r * 0.30)
        lip_h = int(r * 0.16)
    elif mouth == MOUTH_HALF:
        lip_w = int(r * 0.32)
        lip_h = int(r * 0.22)
    else:  # OPEN
        lip_w = int(r * 0.34)
        lip_h = int(r * 0.30)

    draw.ellipse(
        (
            lip_cx - lip_w // 2,
            lip_cy - lip_h // 2,
            lip_cx + lip_w // 2,
            lip_cy + lip_h // 2,
        ),
        fill=(220, 50, 50),
        outline=(120, 20, 20),
        width=3,
    )

    # 回転 (少し斜めにする)
    rotated = img.rotate(angle, resample=Image.BICUBIC, expand=False)
    return rotated


@lru_cache(maxsize=8)
def get_punpun(
    size: tuple[int, int] = (280, 280),
    mouth: str = MOUTH_CLOSED,
) -> Image.Image:
    """ぷんぷん画像を取得。ユーザー提供があればそれを使う。"""
    real = ASSETS_DIR / "characters" / f"punpun_{mouth}.png"
    if real.exists():
        try:
            return Image.open(real).convert("RGBA").resize(size, Image.LANCZOS)
        except Exception:
            pass
    # フォールバック: 単一画像しかないなら流用
    fallback = ASSETS_DIR / "characters" / "punpun.png"
    if fallback.exists() and mouth == MOUTH_CLOSED:
        try:
            return Image.open(fallback).convert("RGBA").resize(size, Image.LANCZOS)
        except Exception:
            pass
    return _draw_punpun(size=size, mouth=mouth)


def get_mouth_frame_for_audio(
    audio_amplitude: float,
    *,
    thresholds: tuple[float, float] = (0.05, 0.25),
) -> str:
    """音量 [0, 1] から口の状態を返す。

    - 静かな時 (< thresholds[0]) → 閉
    - 中くらい → 半開
    - 大きい → 全開
    """
    if audio_amplitude < thresholds[0]:
        return MOUTH_CLOSED
    if audio_amplitude < thresholds[1]:
        return MOUTH_HALF
    return MOUTH_OPEN


if __name__ == "__main__":
    for m in (MOUTH_CLOSED, MOUTH_HALF, MOUTH_OPEN):
        img = _draw_punpun(mouth=m)
        img.save(f"/tmp/punpun_{m}.png")
        print(f"/tmp/punpun_{m}.png")
