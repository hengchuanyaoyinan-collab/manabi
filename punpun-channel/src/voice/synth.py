"""音声合成の高レベルインターフェース。
台本のシーン全部をループで音声化し、各シーンの再生時間を埋める。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.types import VideoScript
from src.voice.voicevox_client import VoiceVoxClient
from src.voice.openjtalk_fallback import is_available as has_openjtalk
from src.voice.openjtalk_fallback import speak_to_file as openjtalk_speak


def _audio_duration(path: Path) -> float:
    """ffprobe で wav/mp3 の長さを返す (秒)。"""
    out = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def synthesize_script(
    script: VideoScript,
    out_dir: Path,
    use_voicevox: bool = True,
) -> VideoScript:
    """各シーンの音声を作る。シーンの audio_path / duration を更新して返す。"""
    out_dir.mkdir(parents=True, exist_ok=True)

    client: VoiceVoxClient | None = None
    if use_voicevox:
        client = VoiceVoxClient()
        if not client.health():
            client = None

    if client is None:
        if not has_openjtalk():
            raise RuntimeError(
                "音声合成エンジンが見つかりません。VOICEVOX を起動するか、"
                "open-jtalk をインストールしてください。"
            )

    for scene in script.scenes:
        out_path = out_dir / f"scene_{scene.index:04d}.wav"
        if client:
            client.speak_to_file(scene.text, out_path)
        else:
            openjtalk_speak(scene.text, out_path)
        scene.audio_path = str(out_path)
        scene.duration_seconds = _audio_duration(out_path)
    return script


def concatenate_audio(script: VideoScript, out_path: Path) -> Path:
    """全シーンの音声を 1 ファイルに結合 (ffmpeg concat)。"""
    if not script.scenes or not all(s.audio_path for s in script.scenes):
        raise RuntimeError("scenes に audio_path が無いものがあります")

    list_file = out_path.with_suffix(".txt")
    list_file.write_text(
        "\n".join(f"file '{Path(s.audio_path).resolve()}'" for s in script.scenes),
        encoding="utf-8",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(out_path),
        ],
        check=True, capture_output=True,
    )
    list_file.unlink(missing_ok=True)
    return out_path


if __name__ == "__main__":
    # 軽い動作確認
    print("voicevox_client present:", VoiceVoxClient().health())
    print("openjtalk available:", has_openjtalk())
