# 環境構築手順

次回セッションで、ここから順番に進める。

## ⚠️ 前提

- Windows 10/11
- Claude Code を使用（Max プラン契約済み）
- 非エンジニア（コマンドはコピペで動くように指示）

## インストールするもの

| # | ソフト | 用途 | 入手元 |
|---|---|---|---|
| 1 | Node.js | Remotion実行 | https://nodejs.org/ |
| 2 | Python | 各種スクリプト | https://www.python.org/ |
| 3 | FFmpeg | 動画エンコード | https://ffmpeg.org/ |
| 4 | VOICEVOX | 音声合成 | https://voicevox.hiroshiba.jp/ |
| 5 | Git | バージョン管理 | https://git-scm.com/ |

## 手順

### 1. Node.js インストール

1. https://nodejs.org/ へアクセス
2. 「LTS」版をダウンロード（推奨版）
3. インストーラを実行、全部「次へ」でOK
4. 確認: PowerShellで `node --version` → v20.x 等が表示されればOK

### 2. Python インストール

1. https://www.python.org/downloads/ へアクセス
2. 最新安定版をダウンロード
3. インストーラ実行時、**必ず「Add Python to PATH」にチェック**
4. 確認: `python --version` → 3.11.x 等

### 3. FFmpeg インストール

#### 簡単な方法: winget使用（Windows 11推奨）
PowerShellで:
```powershell
winget install Gyan.FFmpeg
```

#### 手動の場合
1. https://www.gyan.dev/ffmpeg/builds/ から `ffmpeg-release-essentials.zip` ダウンロード
2. `C:\ffmpeg` に解凍
3. 環境変数PATHに `C:\ffmpeg\bin` を追加
4. 確認: `ffmpeg -version`

### 4. VOICEVOX インストール

1. https://voicevox.hiroshiba.jp/ へアクセス
2. Windows版ダウンロード（.exe）
3. インストーラ実行
4. 起動して動作確認
5. キャラクター選定（推奨候補）:
   - **春日部つむぎ**（高め・少女っぽい）
   - **四国めたん**（高め・元気）
   - **剣崎雌雄**（高め・中性的・個性強い）
   - ずんだもんは競合で飽和しているため避ける

### 5. Git インストール（多分既にあるはず）

```powershell
git --version
```

無ければ https://git-scm.com/ からダウンロード。

## チェックリスト

次回セッションの最初に以下を実行して確認:

```powershell
node --version      # v20.x
python --version    # 3.11.x
ffmpeg -version     # ffmpeg version 6.x
git --version       # git version 2.x
```

VOICEVOX は GUI アプリなので、起動してキャラが選択画面に出ればOK。

## 次のステップ

環境が整ったら → `02-architecture.md` を見てシステム全体像を理解 → `03-workflow.md` で実装開始。
