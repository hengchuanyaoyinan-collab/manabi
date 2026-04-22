"""open-jtalk フォールバック (Linux サンドボックス用テスト)。

VOICEVOX は Windows GUI アプリのため、開発環境では使えない。
このモジュールは VOICEVOX が無い時に open-jtalk で代替音声を作る。

本番 (ユーザー Windows PC) では使わない。
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

OPEN_JTALK = shutil.which("open_jtalk")
DICT = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"


def is_available() -> bool:
    return bool(OPEN_JTALK and Path(DICT).exists() and Path(VOICE).exists())


def speak_to_file(text: str, out_path: Path) -> Path:
    if not is_available():
        raise RuntimeError("open-jtalk is not installed in this environment")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write(text)
        text_path = f.name
    try:
        subprocess.run(
            [
                OPEN_JTALK,
                "-x", DICT,
                "-m", VOICE,
                "-r", "1.0",
                "-ow", str(out_path),
                text_path,
            ],
            check=True,
            capture_output=True,
        )
    finally:
        Path(text_path).unlink(missing_ok=True)
    return out_path
