"""アニメーション付き動画生成。

各シーンをフレーム列として生成:
- 背景: Ken Burns (ゆっくりズームイン)
- 吹き出し: 冒頭 0.3s でポップイン
- ぷんぷん: 音量に応じて口パク + ふわふわ上下

フレーム列を FFmpeg で MP4 化。音声を多重化。
"""
from __future__ import annotations

import math
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.config import ASSETS_DIR, style_config
from src.models import VideoScript
from src.video.character import (
    MOUTH_CLOSED,
    MOUTH_HALF,
    MOUTH_OPEN,
    get_mouth_frame_for_audio,
    get_punpun,
)


# フォント解決は assembler のを流用
from src.video.assembler import _find_font, _wrap_text


# ---- 音声の振幅エンベロープ ----

def _audio_envelope(wav_path: Path, fps: int = 30) -> list[float]:
    """WAV の RMS エンベロープを fps で取得。正規化して [0, 1]。"""
    with wave.open(str(wav_path), "rb") as w:
        n_channels = w.getnchannels()
        sample_width = w.getsampwidth()
        sample_rate = w.getframerate()
        n_frames = w.getnframes()
        raw = w.readframes(n_frames)

    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}[sample_width]
    audio = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)
    # Normalize to -1..1
    max_val = float(np.iinfo(dtype).max) if dtype != np.uint8 else 128.0
    audio = audio / max_val

    # frame (1/fps 秒) ごとの RMS
    samples_per_frame = int(sample_rate / fps)
    num_frames = int(math.ceil(len(audio) / samples_per_frame))
    envelope: list[float] = []
    for i in range(num_frames):
        chunk = audio[i * samples_per_frame : (i + 1) * samples_per_frame]
        if len(chunk) == 0:
            envelope.append(0.0)
            continue
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        envelope.append(min(1.0, rms * 4.0))  # *4 で増幅
    return envelope


# ---- シーン単位のフレーム生成 ----

def _ease_out(t: float) -> float:
    """イージング: 最初速く、最後ゆっくり。"""
    return 1 - (1 - t) ** 3


def _draw_speech_bubble_scaled(
    canvas: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    progress: float,  # 0..1 のポップイン
) -> None:
    """吹き出しを描く (progress で大きさ + 透明度変化)。"""
    if not text or progress <= 0:
        return
    from src.video.assembler import _draw_speech_bubble
    if progress >= 1.0:
        _draw_speech_bubble(canvas, text, font=font)
        return
    # 小さめの一時キャンバスに描いて拡大
    tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    _draw_speech_bubble(tmp, text, font=font)
    # スケーリング (ポップ)
    scale = 0.6 + 0.4 * progress
    new_size = (int(tmp.width * scale), int(tmp.height * scale))
    if new_size[0] > 0 and new_size[1] > 0:
        scaled = tmp.resize(new_size, Image.LANCZOS)
        # 中央に配置 (bubble は左下なので、縮小時に少し中心へ寄せる)
        offset_x = (tmp.width - new_size[0]) // 2
        offset_y = tmp.height - new_size[1] - (tmp.height - new_size[1]) // 4
        # 透明度
        alpha = int(255 * progress)
        if alpha < 255:
            alpha_layer = scaled.split()[-1]
            alpha_layer = alpha_layer.point(lambda p: int(p * progress))
            scaled.putalpha(alpha_layer)
        canvas.alpha_composite(scaled, (offset_x, offset_y))


def render_scene_frames(
    background: Image.Image,
    text: str,
    audio_envelope: list[float],
    *,
    fps: int = 30,
    duration: float,
    width: int = 1920,
    height: int = 1080,
    ken_burns: bool = True,
) -> list[Image.Image]:
    """1 シーンの全フレームを返す。"""
    cfg = style_config()
    font = _find_font(cfg["speechBubble"]["fontSize"])
    char_size = (cfg["character"]["size"]["width"], cfg["character"]["size"]["height"])

    total_frames = max(1, int(duration * fps))
    pop_frames = min(total_frames, int(0.35 * fps))  # 0.35 秒でポップイン
    frames: list[Image.Image] = []

    # 背景を少し大きくして (115%) Ken Burns 用
    ken_start_scale = 1.0
    ken_end_scale = 1.10 if ken_burns else 1.0
    bg_w, bg_h = background.size
    # 一旦ベースサイズに合わせる
    if (bg_w, bg_h) != (width, height):
        ratio = max(width / bg_w, height / bg_h) * ken_end_scale
        base = background.resize(
            (int(bg_w * ratio), int(bg_h * ratio)),
            Image.LANCZOS,
        )
    else:
        ratio = ken_end_scale
        base = background.resize(
            (int(width * ratio), int(height * ratio)),
            Image.LANCZOS,
        )

    for frame_idx in range(total_frames):
        t = frame_idx / max(1, total_frames - 1)

        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        # Ken Burns: 徐々に拡大・少しパン
        if ken_burns:
            cur_scale = ken_start_scale + (ken_end_scale - ken_start_scale) * t
            cur_bg = base.resize(
                (int(width * cur_scale), int(height * cur_scale)),
                Image.LANCZOS,
            )
            # 中心から少しパン (右下方向)
            pan_x = int((cur_bg.width - width) * (0.3 + 0.4 * t))
            pan_y = int((cur_bg.height - height) * (0.3 + 0.4 * t))
            pan_x = max(0, min(cur_bg.width - width, pan_x))
            pan_y = max(0, min(cur_bg.height - height, pan_y))
            cropped = cur_bg.crop((pan_x, pan_y, pan_x + width, pan_y + height))
            canvas.paste(cropped.convert("RGBA"), (0, 0))
        else:
            # 中央クロップ
            left = (base.width - width) // 2
            top = (base.height - height) // 2
            canvas.paste(
                base.crop((left, top, left + width, top + height)).convert("RGBA"),
                (0, 0),
            )

        # 吹き出し (ポップイン)
        bubble_progress = min(1.0, frame_idx / pop_frames) if pop_frames > 0 else 1.0
        _draw_speech_bubble_scaled(canvas, text, font, _ease_out(bubble_progress))

        # ぷんぷん (口パク + ふわふわ)
        amp = audio_envelope[frame_idx] if frame_idx < len(audio_envelope) else 0.0
        mouth = get_mouth_frame_for_audio(amp)
        bob = int(4 * math.sin(frame_idx / fps * 2 * math.pi * 1.3))  # ~1.3Hz
        punpun = get_punpun(size=char_size, mouth=mouth)

        cx = width - char_size[0] - cfg["character"]["offset"]["x"]
        cy = height - char_size[1] - cfg["character"]["offset"]["y"] + bob
        canvas.alpha_composite(punpun, (cx, cy))

        frames.append(canvas.convert("RGB"))

    return frames


def render_scene_video(
    background: Image.Image,
    text: str,
    audio_path: Path,
    duration: float,
    out_path: Path,
    *,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """1 シーンのアニメーション付き動画 (音声入り) を作る。"""
    envelope = _audio_envelope(audio_path, fps=fps)
    frames = render_scene_frames(
        background, text, envelope,
        fps=fps, duration=duration, width=width, height=height,
    )

    # 一時 PNG 連番にしてから ffmpeg で MP4 化
    with tempfile.TemporaryDirectory() as tmpd:
        for i, f in enumerate(frames):
            f.save(f"{tmpd}/f{i:06d}.png")

        # 無音動画
        silent = Path(tmpd) / "silent.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", f"{tmpd}/f%06d.png",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "20",
                str(silent),
            ],
            check=True, capture_output=True,
        )

        # 音声多重化
        out_path.parent.mkdir(parents=True, exist_ok=True)
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


def render_animated_video(
    script: VideoScript,
    backgrounds: list[Image.Image],
    out_path: Path,
    *,
    fps: int = 24,
    width: int = 1920,
    height: int = 1080,
    work_dir: Path | None = None,
) -> Path:
    """全シーンをアニメ付きで連結した MP4 を作る。

    各シーンごとに小さい MP4 を作り、最後に concat 多重化。
    """
    if work_dir is None:
        work_dir = out_path.parent / "_anim_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    scene_videos: list[Path] = []
    for scene, bg in zip(script.scenes, backgrounds, strict=True):
        if not scene.audio_path or scene.duration_seconds is None:
            raise RuntimeError(f"scene {scene.index} has no audio")
        mp4 = work_dir / f"scene_{scene.index:04d}.mp4"
        if not mp4.exists():
            render_scene_video(
                bg, scene.text, Path(scene.audio_path),
                duration=scene.duration_seconds,
                out_path=mp4,
                fps=fps, width=width, height=height,
            )
        scene_videos.append(mp4)

    # concat
    list_file = work_dir / "scenes_list.txt"
    list_file.write_text(
        "\n".join(f"file '{m.resolve()}'" for m in scene_videos),
        encoding="utf-8",
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_path),
        ],
        check=True, capture_output=True,
    )
    return out_path
