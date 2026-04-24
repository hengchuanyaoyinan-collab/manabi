"""ElevenLabs 声クローン合成。

VOICEVOX の代替 / 上位。あなたのボイチェン後の声を学習させて
AI で再生成できる。

事前準備:
1. https://elevenlabs.io でアカウント作成 (Starter $5/月)
2. 右上メニュー → API → API キーコピー
3. 音声クローン作成:
   - Voices → Add a New Voice → Instant Voice Cloning
   - 過去動画の音声ファイル (10 秒以上、ノイズ少なめ) をアップロード
   - Voice ID をコピー
4. .env に追加:
   ELEVENLABS_API_KEY=sk_xxx
   ELEVENLABS_VOICE_ID=abc123

使い方:
    from src.voice.elevenlabs_client import ElevenLabsClient
    c = ElevenLabsClient()
    c.speak_to_file("セリフ", Path("out.mp3"))
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from src.config import env


class ElevenLabsClient:
    """ElevenLabs TTS クライアント。"""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
        model: str = "eleven_multilingual_v2",
    ):
        self.api_key = api_key or env("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or env("ELEVENLABS_VOICE_ID")
        self.model = model
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY が未設定")
        if not self.voice_id:
            raise RuntimeError("ELEVENLABS_VOICE_ID が未設定")

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "audio/mpeg",
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def speak_to_file(
        self,
        text: str,
        out_path: Path,
        *,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.3,
        use_speaker_boost: bool = True,
    ) -> Path:
        """テキストを音声ファイルに。MP3 で保存。"""
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}"
        payload: dict[str, Any] = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost,
            },
        }
        r = requests.post(url, json=payload, headers=self._headers(), timeout=120)
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        return out_path

    def list_voices(self) -> list[dict]:
        r = requests.get(
            f"{self.BASE_URL}/voices",
            headers={"xi-api-key": self.api_key},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("voices", [])

    def get_subscription(self) -> dict:
        r = requests.get(
            f"{self.BASE_URL}/user/subscription",
            headers={"xi-api-key": self.api_key},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()


def is_available() -> bool:
    return bool(env("ELEVENLABS_API_KEY") and env("ELEVENLABS_VOICE_ID"))


if __name__ == "__main__":
    import sys
    try:
        c = ElevenLabsClient()
    except RuntimeError as e:
        print(e)
        sys.exit(1)
    sub = c.get_subscription()
    print(f"Tier: {sub.get('tier')}")
    print(f"Char used: {sub.get('character_count')}/{sub.get('character_limit')}")
    if len(sys.argv) > 1:
        out = Path("/tmp/eleven_test.mp3")
        c.speak_to_file(sys.argv[1], out)
        print(f"OK: {out}")
