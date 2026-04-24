# 🪟 Windows セットアップ完全ガイド

**0 から始めて、動画 1 本作れるまで。所要 45 分。**

コマンドは**全部コピペで動く**。つまづいたらスクショ送ってください。

---

## 📋 Step 0: 何をするか

1. ツール 3 つインストール (Python, Git, FFmpeg) — **15 分**
2. このコードを取得 — **5 分**
3. Python 環境準備 — **10 分**
4. テスト動画生成 — **10 分**
5. 出来た動画を再生 — **1 分**

合計 45 分。

---

## 📌 Step 1: ツール 3 つインストール

### ① Python

https://www.python.org/downloads/ を開く
→ 黄色いボタン「Download Python 3.xx.x」をクリック
→ 落ちた `.exe` をダブルクリック
→ **⚠️ 一番下の「Add Python to PATH」に必ずチェック**
→ 「Install Now」
→ 完了まで 2〜3 分

### ② Git

https://git-scm.com/download/win を開く
→ 自動でダウンロード始まる
→ `.exe` を実行
→ 全部「Next」で OK (設定はデフォルトで大丈夫)

### ③ FFmpeg (一番楽な方法)

Windows スタート → `powershell` と入力 → **右クリック → 「管理者として実行」**
黒い画面で以下をコピペして Enter:
```powershell
winget install Gyan.FFmpeg
```
`Do you agree...?` と聞かれたら `y` を押して Enter。
完了まで 3〜5 分。

### ✅ 確認

PowerShell を**一度閉じて新しく開く** (管理者でなくてよい) → 以下を 1 行ずつコピペ。全部バージョンが出れば成功:
```powershell
python --version
git --version
ffmpeg -version
```

---

## 📌 Step 2: コードを取得

PowerShell で以下を順にコピペ:

```powershell
cd $env:USERPROFILE
git clone https://github.com/hengchuanyaoyinan-collab/manabi.git
cd manabi
git checkout claude/add-video-creation-gZ3Et
cd punpun-channel
```

`punpun-channel` フォルダに入れれば OK。

---

## 📌 Step 3: Python 環境準備

PowerShell (punpun-channel フォルダ内) で:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

最後のコマンドは数分かかる (cartopy, geopandas 等をダウンロード)。

### ⚠️ もしエラーが出たら:
- `Microsoft Visual C++ 14.0 or greater is required.` → https://visualstudio.microsoft.com/visual-cpp-build-tools/ から C++ Build Tools をインストール
- その他のエラー → スクショをチャットに送る

---

## 📌 Step 4: テスト動画を生成

```powershell
python src\orchestrator.py --script test_data\chinghis_khan_v4.json --test --no-voicevox
```

10〜15 分かかります (画像を Wikipedia から取ってくる、音声作る、動画組み立てる)。

**ログに以下が出ればOK:**
```
✅ Done. C:\...\output\test\xxx\report.json
```

---

## 📌 Step 5: 動画を再生

```powershell
start output\test
```
一番新しいフォルダ開いて、`video.mp4` をダブルクリック。

---

## 🎙 Step 6 (任意): VOICEVOX で声を本物に

### インストール

https://voicevox.hiroshiba.jp/ から Windows 版ダウンロード。
普通にインストーラ実行。

### 起動

スタートメニューから VOICEVOX 起動。キャラ選択画面が出たら起動完了。
**VOICEVOX を起動したままにしておく**。

### 再生成

PowerShell で:
```powershell
python src\orchestrator.py --script test_data\chinghis_khan_v4.json --test
```
(`--no-voicevox` を外すだけ。VOICEVOX の声になる)

---

## 🎵 Step 7 (任意): BGM と SE を配置

1. **BGM**: https://dova-s.jp/ から好きな曲を 3〜7 曲ダウンロード
   - `assets\bgm\` に配置 (ファイル名に `op_`, `drama_`, `epic_`, `sad_`, `dark_`, `peaceful_`, `uplift_` のいずれかを含める)
   - 詳細は `assets\bgm\README.md`

2. **SE**: https://soundeffect-lab.info/ から 3〜5 個ダウンロード
   - `assets\se\` に配置 (ファイル名に `chapter_`, `shock_`, `flash_` を含める)

素材を置いた後は、パイプライン実行時に自動ミックスされます。

---

## 🔑 Step 8 (任意): OpenAI 画像生成を有効化

1. https://platform.openai.com でアカウント作成 + API キー発行
2. `notepad .env` で .env を開く
3. `OPENAI_API_KEY=sk-...` に新しいキーを書く (保存して閉じる)

以降のパイプライン実行時に自動で**シーン専用イラスト**が生成されます。

---

## 🎤 Step 9 (任意): ElevenLabs 声クローン

1. https://elevenlabs.io で Starter プラン契約 ($5/月)
2. 左メニュー Voices → Add a New Voice → Instant Voice Cloning
3. 過去動画の音声 10 秒以上をアップロード
4. Voice ID と API キーを取得
5. `.env` に追加:
   ```
   ELEVENLABS_API_KEY=sk_xxx
   ELEVENLABS_VOICE_ID=xxx
   ```

**本物のあなたの声で動画が作れます。**

---

## 🤖 Step 10 (任意): 毎日自動投稿

1. YouTube 認証:
   ```powershell
   python src\upload\youtube_oauth.py
   ```
   (Google Cloud Console で OAuth クライアント作成が必要。詳細は `docs\01-setup.md`)

2. 自動実行登録:
   ```powershell
   .\scripts\setup-windows-task.ps1
   ```
   PowerShell を管理者で実行すること。
   毎日 19:00 に自動で 1 本投稿される。

---

## 🆘 困ったら

| 症状 | 対処 |
|---|---|
| Python が見つからない | PATH 通ってない。`.venv\Scripts\activate` してるか確認 |
| git が見つからない | インストール失敗。Step 1 ② 再実行 |
| cartopy インストールで詰まる | VC++ Build Tools 入れる |
| pip install が遅い | 正常。5〜10 分待つ |
| VOICEVOX 繋がらない | VOICEVOX が起動してるか確認 |
| Wikipedia 画像来ない | ネット接続確認、VPN 切る |
| その他 | スクショをチャットに送る |

---

## 📞 サポート

困ったらそのまま私に言ってください。エラーメッセージをそのままコピペで OK。

今すぐ始めるなら **Step 1** から。
