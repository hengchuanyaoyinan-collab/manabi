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


def _apply_fade(img: Image.Image, alpha: float) -> Image.Image:
    """alpha=1 そのまま、alpha=0 全黒 に補間。"""
    if alpha >= 0.999:
        return img
    if alpha <= 0.001:
        return Image.new("RGB", img.size, (0, 0, 0))
    # numpy で高速に
    import numpy as np
    arr = np.asarray(img, dtype=np.float32) * alpha
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


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
    fade_in: float = 0.15,
    fade_out: float = 0.10,
) -> list[Image.Image]:
    """1 シーンの全フレームを返す。
    fade_in/fade_out 秒数で黒フェード。
    """
    cfg = style_config()
    font = _find_font(cfg["speechBubble"]["fontSize"])
    char_size = (cfg["character"]["size"]["width"], cfg["character"]["size"]["height"])

    total_frames = max(1, int(duration * fps))
    pop_frames = min(total_frames, int(0.35 * fps))  # 0.35 秒でポップイン
    frames: list[Image.Image] = []

    # 背景を 1 回だけ大サイズにスケール (毎フレーム resize すると遅い)
    ken_max_scale = 1.10 if ken_burns else 1.0
    ratio = max(width / background.width, height / background.height) * ken_max_scale
    max_bg = background.resize(
        (int(background.width * ratio), int(background.height * ratio)),
        Image.LANCZOS,
    ).convert("RGBA")

    for frame_idx in range(total_frames):
        t = frame_idx / max(1, total_frames - 1)

        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        # Ken Burns: max_bg から徐々にタイト化する viewport を切り出す
        if ken_burns:
            # t=0 で最大視野 (max_bg 全体に近い) → t=1 で狭い視野 (拡大)
            # 仮想ズーム = 1.0 → 1.10
            cur_zoom = 1.0 + (ken_max_scale - 1.0) * t
            # viewport サイズ = max_bg size / cur_zoom * (ken_max_scale)
            # シンプルに: viewport 幅 = width * (ken_max_scale / cur_zoom)
            vp_scale = ken_max_scale / cur_zoom
            vp_w = int(width * vp_scale)
            vp_h = int(height * vp_scale)
            pan_x = int((max_bg.width - vp_w) * (0.3 + 0.4 * t))
            pan_y = int((max_bg.height - vp_h) * (0.3 + 0.4 * t))
            pan_x = max(0, min(max_bg.width - vp_w, pan_x))
            pan_y = max(0, min(max_bg.height - vp_h, pan_y))
            cropped = max_bg.crop((pan_x, pan_y, pan_x + vp_w, pan_y + vp_h))
            if (vp_w, vp_h) != (width, height):
                cropped = cropped.resize((width, height), Image.BILINEAR)
            canvas.paste(cropped, (0, 0))
        else:
            left = (max_bg.width - width) // 2
            top = (max_bg.height - height) // 2
            canvas.paste(max_bg.crop((left, top, left + width, top + height)), (0, 0))

        # 吹き出し (ポップイン)
        bubble_progress = min(1.0, frame_idx / pop_frames) if pop_frames > 0 else 1.0
        _draw_speech_bubble_scaled(canvas, text, font, _ease_out(bubble_progress))

        # ぷんぷん (口パク + ふわふわ)
        # 口パクを少しスムーズに (前後 3 フレームの最大を採用して flicker 回避)
        window = audio_envelope[max(0, frame_idx - 2) : frame_idx + 3]
        amp = max(window) if window else 0.0
        mouth = get_mouth_frame_for_audio(amp)
        bob = int(4 * math.sin(frame_idx / fps * 2 * math.pi * 1.3))  # ~1.3Hz
        punpun = get_punpun(size=char_size, mouth=mouth)

        cx = width - char_size[0] - cfg["character"]["offset"]["x"]
        cy = height - char_size[1] - cfg["character"]["offset"]["y"] + bob
        canvas.alpha_composite(punpun, (cx, cy))

        rgb = canvas.convert("RGB")

        # フェード (シーン頭尾に黒からのフェードを入れて繋ぎを自然に)
        fade_in_frames = int(fade_in * fps)
        fade_out_frames = int(fade_out * fps)
        if frame_idx < fade_in_frames and fade_in_frames > 0:
            alpha = frame_idx / fade_in_frames
            rgb = _apply_fade(rgb, alpha)
        elif frame_idx >= total_frames - fade_out_frames and fade_out_frames > 0:
            alpha = max(0.0, (total_frames - 1 - frame_idx) / fade_out_frames)
            rgb = _apply_fade(rgb, alpha)

        frames.append(rgb)

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


def _render_one_scene_wrapper(args: tuple) -> str:
    """multiprocessing 用の thin wrapper (pickle できる引数で受ける)。"""
    (bg_bytes, bg_mode, bg_size, text, audio_path, duration,
     out_path, fps, width, height) = args
    from io import BytesIO
    bg = Image.frombytes(bg_mode, bg_size, bg_bytes)
    render_scene_video(
        bg, text, Path(audio_path),
        duration=duration,
        out_path=Path(out_path),
        fps=fps, width=width, height=height,
    )
    return str(out_path)


def render_animated_video(
    script: VideoScript,
    backgrounds: list[Image.Image],
    out_path: Path,
    *,
    fps: int = 24,
    width: int = 1920,
    height: int = 1080,
    work_dir: Path | None = None,
    parallel: int = 3,
) -> Path:
    """全シーンをアニメ付きで連結した MP4 を作る。

    各シーンごとに小さい MP4 を作り、最後に concat 多重化。
    parallel > 1 で multiprocessing 並列化。
    """
    if work_dir is None:
        work_dir = out_path.parent / "_anim_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # 未生成のシーンを洗い出し
    tasks: list[tuple] = []
    scene_videos: list[Path] = []
    for scene, bg in zip(script.scenes, backgrounds, strict=True):
        if not scene.audio_path or scene.duration_seconds is None:
            raise RuntimeError(f"scene {scene.index} has no audio")
        mp4 = work_dir / f"scene_{scene.index:04d}.mp4"
        scene_videos.append(mp4)
        if not mp4.exists():
            # pickle 可能な形に変換 (Image は mp に渡しにくい)
            bg_converted = bg.convert("RGBA")
            tasks.append((
                bg_converted.tobytes(), bg_converted.mode, bg_converted.size,
                scene.text, scene.audio_path, scene.duration_seconds,
                str(mp4), fps, width, height,
            ))

    if tasks:
        if parallel > 1:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(max_workers=parallel) as ex:
                futures = {ex.submit(_render_one_scene_wrapper, t): t for t in tasks}
                for f in as_completed(futures):
                    f.result()
        else:
            for t in tasks:
                _render_one_scene_wrapper(t)

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
