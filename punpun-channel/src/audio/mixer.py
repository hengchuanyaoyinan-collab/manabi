"""BGM / SE 音響ミキサ。

ナレーション (narration.wav) に以下をミックスする:
1. BGM: 章ごとに切り替え、音量 -18dB (ナレーション時は -24dB にダッキング)
2. SE: 章切替・衝撃シーンで配置

assets/bgm/ と assets/se/ に音素材を置いて使う。
"""
from __future__ import annotations

import random
import shutil
import subprocess
import wave
from pathlib import Path

from src.config import ASSETS_DIR
from src.models import VideoScript


BGM_DIR = ASSETS_DIR / "bgm"
SE_DIR = ASSETS_DIR / "se"


# ========== BGM プール (章タイプ別) ==========

# 章番号ごとに使う BGM のカテゴリ
# ファイル名サフィックスで分類: _op_*.mp3 / _drama_*.mp3 / _peaceful_*.mp3 等
BGM_CATEGORY_BY_CHAPTER = {
    0: "op",          # OP (緊張感)
    1: "peaceful",    # 生い立ち (穏やか)
    2: "drama",       # 転機 (テンポ UP)
    3: "epic",        # 全盛期 (オーケストラ風)
    4: "dark",        # 狂気 (重い)
    5: "sad",         # 最期 (静か)
    6: "uplift",      # まとめ (前向き)
}


def _list_bgm(category: str) -> list[Path]:
    """assets/bgm/ から指定カテゴリの音源を探す。"""
    if not BGM_DIR.exists():
        return []
    patterns = [f"*{category}*.mp3", f"*{category}*.wav", f"*{category}*.m4a"]
    files: list[Path] = []
    for pat in patterns:
        files.extend(BGM_DIR.glob(pat))
    return sorted(files)


def _pick_bgm(category: str, seed: str = "") -> Path | None:
    """カテゴリ一致の BGM を 1 つ選ぶ (seed で決定的に)。"""
    files = _list_bgm(category)
    if not files:
        # フォールバック: 汎用 BGM
        files = list(BGM_DIR.glob("*.mp3")) + list(BGM_DIR.glob("*.wav"))
    if not files:
        return None
    if seed:
        idx = hash(seed) % len(files)
        return files[idx]
    return random.choice(files)


# ========== SE プール ==========

def _pick_se(kind: str) -> Path | None:
    """SE を 1 つ選ぶ。kind = 'chapter' / 'shock' / 'flash' / 'intro'。"""
    if not SE_DIR.exists():
        return None
    files = list(SE_DIR.glob(f"*{kind}*.mp3")) + list(SE_DIR.glob(f"*{kind}*.wav"))
    if not files:
        # デフォルト
        files = list(SE_DIR.glob("default*"))
    return files[0] if files else None


# ========== BGM 生成 (章ごと切替) ==========

def build_bgm_track(
    script: VideoScript,
    out_path: Path,
    *,
    narration_duration_sec: float,
    topic: str = "",
    bgm_volume_db: float = -20.0,
    ducking_db: float = -28.0,
) -> Path | None:
    """章ごとに BGM を切り替えた長尺 BGM トラックを作る。
    narration の長さに合わせてトリム。
    """
    if not BGM_DIR.exists() or not any(BGM_DIR.iterdir()):
        return None

    # 章ごとの持続時間を算出
    chapter_durations: dict[int, float] = {}
    for scene in script.scenes:
        if scene.duration_seconds:
            chapter_durations[scene.chapter] = (
                chapter_durations.get(scene.chapter, 0.0) + scene.duration_seconds
            )

    if not chapter_durations:
        return None

    # 各章の BGM ファイルを決定
    segments: list[tuple[Path, float]] = []
    for ch_idx in sorted(chapter_durations.keys()):
        cat = BGM_CATEGORY_BY_CHAPTER.get(ch_idx, "peaceful")
        bgm = _pick_bgm(cat, seed=f"{topic}_{ch_idx}")
        dur = chapter_durations[ch_idx]
        if bgm:
            segments.append((bgm, dur))

    if not segments:
        return None

    # ffmpeg で連結 (loop + trim で長さに合わせる)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = out_path.parent / "_bgm_tmp"
    tmp_dir.mkdir(exist_ok=True)

    segment_files: list[Path] = []
    for i, (src, dur) in enumerate(segments):
        seg_out = tmp_dir / f"seg_{i:02d}.mp3"
        # ループしつつ指定長にトリム、フェードイン/アウト 1 秒
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-stream_loop", "-1", "-i", str(src),
                "-t", f"{dur:.2f}",
                "-af", f"volume={bgm_volume_db}dB,afade=t=in:d=1,afade=t=out:st={max(0, dur-1):.2f}:d=1",
                "-c:a", "libmp3lame",
                str(seg_out),
            ],
            check=True, capture_output=True,
        )
        segment_files.append(seg_out)

    # 全セグメントを連結
    list_file = tmp_dir / "bgm_list.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in segment_files),
        encoding="utf-8",
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:a", "libmp3lame",
            "-t", f"{narration_duration_sec:.2f}",
            str(out_path),
        ],
        check=True, capture_output=True,
    )
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return out_path


# ========== 最終ミックス (ナレーション + BGM) ==========

def mix_narration_and_bgm(
    narration_path: Path,
    bgm_path: Path | None,
    out_path: Path,
    *,
    narration_gain_db: float = 0.0,
    bgm_gain_db: float = -6.0,
) -> Path:
    """ナレーションと BGM をミックス。
    ナレーションが鳴る時だけ BGM をダッキング (sidechaincompress)。
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if bgm_path is None or not bgm_path.exists():
        # BGM 無し: ナレーションをそのままコピー
        shutil.copy(narration_path, out_path)
        return out_path

    # sidechaincompress = ナレーションの音量に応じて BGM を下げる
    filter_complex = (
        f"[0:a]volume={narration_gain_db}dB,asplit=2[narr][narr_key];"
        f"[1:a]volume={bgm_gain_db}dB[bgm];"
        f"[bgm][narr_key]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=300[bgm_ducked];"
        f"[narr][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=0[out]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(narration_path),
            "-i", str(bgm_path),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k",
            str(out_path),
        ],
        check=True, capture_output=True,
    )
    return out_path


# ========== SE 差込 ==========

def overlay_se(
    base_audio: Path,
    se_placements: list[tuple[float, Path]],
    out_path: Path,
    *,
    se_gain_db: float = -3.0,
) -> Path:
    """base_audio (ミックス済ナレ+BGM) に SE を指定時刻で重ねる。
    se_placements = [(start_sec, se_file), ...]
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not se_placements:
        shutil.copy(base_audio, out_path)
        return out_path

    # ffmpeg filter を組み立て
    # [0:a] = base
    # [1:a], [2:a], ... = SE inputs
    inputs = ["-i", str(base_audio)]
    filter_parts: list[str] = []
    mix_inputs = ["[0:a]"]

    for i, (start, se_file) in enumerate(se_placements, start=1):
        inputs.extend(["-i", str(se_file)])
        filter_parts.append(
            f"[{i}:a]volume={se_gain_db}dB,adelay={int(start * 1000)}|{int(start * 1000)}[se{i}]"
        )
        mix_inputs.append(f"[se{i}]")

    filter_parts.append(
        f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=0[out]"
    )

    filter_complex = ";".join(filter_parts)

    subprocess.run(
        ["ffmpeg", "-y", *inputs,
         "-filter_complex", filter_complex,
         "-map", "[out]",
         "-c:a", "aac", "-b:a", "192k",
         str(out_path)],
        check=True, capture_output=True,
    )
    return out_path


# ========== SE 配置の自動提案 ==========

def plan_se_placements(script: VideoScript) -> list[tuple[float, str]]:
    """台本から SE を配置すべきタイミングと種類を抽出。
    返り値: [(秒数, SE種類), ...]
    種類は後で _pick_se に渡す。
    """
    placements: list[tuple[float, str]] = []
    current_sec = 0.0
    last_chapter = -1

    for scene in script.scenes:
        dur = scene.duration_seconds or 3.0
        # 章切替の瞬間
        if scene.chapter != last_chapter:
            placements.append((current_sec, "chapter"))
            last_chapter = scene.chapter
        # 衝撃シーン
        if scene.emotion == "shock":
            placements.append((current_sec, "shock"))
        current_sec += dur

    return placements


def resolve_se_placements(
    planned: list[tuple[float, str]]
) -> list[tuple[float, Path]]:
    resolved: list[tuple[float, Path]] = []
    for start, kind in planned:
        se = _pick_se(kind)
        if se:
            resolved.append((start, se))
    return resolved


# ========== 高レベル API ==========

def build_final_audio(
    script: VideoScript,
    narration_path: Path,
    out_path: Path,
    *,
    topic: str = "",
) -> Path:
    """ナレーション + BGM (章別) + SE (自動配置) をミックスした最終音声。"""
    work_dir = out_path.parent / "_audio_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # 長さを取得
    subprocess_result = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1",
         str(narration_path)],
        check=True, capture_output=True, text=True,
    )
    total_duration = float(subprocess_result.stdout.strip())

    # BGM トラック
    bgm_path: Path | None = work_dir / "bgm.mp3"
    bgm_result = build_bgm_track(
        script, bgm_path, narration_duration_sec=total_duration, topic=topic,
    )
    if bgm_result is None:
        bgm_path = None

    # ミックス
    mixed = work_dir / "narration_with_bgm.aac"
    mix_narration_and_bgm(narration_path, bgm_path, mixed)

    # SE 差込
    se_placements = resolve_se_placements(plan_se_placements(script))
    if se_placements:
        overlay_se(mixed, se_placements, out_path)
    else:
        shutil.copy(mixed, out_path)

    return out_path
