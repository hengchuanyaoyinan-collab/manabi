"""YouTube Data API v3 OAuth セットアップ。

初回のみブラウザで認証。トークンは config/youtube-token.json に保存
(.gitignore 済)。

事前準備 (ユーザー):
1. https://console.cloud.google.com で新規プロジェクト作成
2. YouTube Data API v3 を有効化
3. OAuth 同意画面 (External / Testing) を作成し、自分のメールを Test users に追加
4. 認証情報 -> OAuth クライアント ID (デスクトップアプリ) を作成
5. JSON をダウンロードし config/oauth-client.json として保存

その後このスクリプトを実行: python3 src/upload/youtube_oauth.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.config import CONFIG_DIR

CLIENT_SECRETS_PATH = CONFIG_DIR / "oauth-client.json"
TOKEN_PATH = CONFIG_DIR / "youtube-token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def authorize() -> dict:
    """OAuth フローを実行してトークンを保存。"""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("❌ google-auth-oauthlib が未インストールです。pip install -r requirements.txt")
        sys.exit(1)

    if not CLIENT_SECRETS_PATH.exists():
        print(f"❌ {CLIENT_SECRETS_PATH} が見つかりません。")
        print("   Google Cloud Console で OAuth クライアントを作成し、JSON を保存してください。")
        sys.exit(1)

    if TOKEN_PATH.exists():
        print(f"既にトークンがあります: {TOKEN_PATH}")
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds.valid:
            print("✅ 有効です")
            return json.loads(TOKEN_PATH.read_text())

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_PATH), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json())
    print(f"✅ トークン保存: {TOKEN_PATH}")
    return json.loads(TOKEN_PATH.read_text())


def get_credentials():
    """既存トークンから Credentials を返す。なければ None。"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        return None

    if not TOKEN_PATH.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds.valid:
        return creds
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
        return creds
    return None


if __name__ == "__main__":
    authorize()
