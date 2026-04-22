# CLAUDE.md

このファイルは Claude Code がこのプロジェクトで作業する時のガイダンス。
ユーザーは非エンジニアなので、専門用語は避けるか必ず噛み砕いて。

## プロジェクト概要

**ぷんぷんの世事見聞録** - YouTube 歴史解説チャンネルの完全自動化。
1 日 1 本、毎日 19:00 に 20 分の歴史解説動画を自動投稿することを目標とする。

詳細ビジョンは `docs/00-vision.md`、競合分析は `docs/04-competitor-analysis.md`。

## アーキテクチャ

Python (Pillow + FFmpeg) ベースのパイプライン。`src/orchestrator.py` が司令塔。

```
題材選定 (src/generator/topic_selector.py)
    ↓
台本生成 (src/generator/script_generator.py) → claude CLI 経由
    ↓
音声合成 (src/voice/synth.py) → VOICEVOX または open-jtalk
    ↓
画像取得 (src/video/image_fetcher.py) → Wikipedia / いらすとや
    ↓
シーン合成 (src/video/assembler.py) → Pillow
    ↓
MP4 化 (src/video/assembler.py) → FFmpeg concat
    ↓
サムネ生成 (src/video/thumbnail_generator.py)
    ↓
YouTube 投稿 (src/upload/upload_video.py)
    ↓
analytics 記録 (src/analytics.py)
```

## 重要なお作法

### コード規約
- Python 3.11+
- Pydantic v2 で型定義 (`src/models.py`)
- `from __future__ import annotations` を冒頭に
- `pathlib.Path` を使う (str ではなく)
- 設定は `src/config.py` の関数経由 (直接 JSON 読まない)

### 命名規則
- ファイル名: `snake_case.py`
- 関数名: `snake_case`
- クラス名: `PascalCase`
- 定数: `UPPER_SNAKE_CASE`

### よくあるミス
- ❌ `src/types.py` という名前 (Python 標準ライブラリと衝突するので `models.py` に)
- ❌ `claude` CLI を `--max-turns 1` で呼ぶ (haiku が tool 使えず詰まる)
- ❌ stdin 開きっぱなしで `claude` 呼ぶ (warning が混ざる、`stdin=DEVNULL` 必須)

## 動作確認方法

任意のコード変更後:
```bash
# 環境チェック
python3 scripts/check-env.py

# テストパイプライン
python3 src/orchestrator.py --script test_data/elizabeth_bathory_full.json --test --no-voicevox

# シーンだけ確認
python3 scripts/preview-scene.py "テストセリフ" --bg blank
```

成功なら `output/test/{timestamp}/video.mp4` が出来る。

## 作業時の注意

### ユーザーへの説明
- 非エンジニアなので、コマンドは**コピペで動く形**で渡す
- エラーメッセージをそのまま貼られたら、原因と対処を平易な日本語で
- 「とりあえずやってみて」ではなく「まず A、次に B」と段階的に

### Git 運用
- ブランチ: `claude/add-video-creation-gZ3Et` (現状)
- コミット粒度: 機能単位 (1 commit = 1 つの完結した変更)
- コミットメッセージ: 日本語 OK、なぜを書く
- push 前に必ず `python3 scripts/check-env.py` と最低 1 つのテストパイプライン実行

### 出力ファイル
- `output/` は `.gitignore` 済 (動画は重い)
- `assets/cache/` も同様
- `.venv/` も同様
- `test_data/*.json` は tracked (再現性のため)
- `config/youtube-token.json` は絶対コミットしない (.gitignore 済)

## 知っておくべきこと

### claude CLI の使い方
ユーザーは Claude Max 契約済 → API キー不要。
台本生成は `src/generator/script_generator.py` 経由で `claude -p ...` を呼ぶ。
正しい呼び方:
```python
cmd = [
    "claude", "-p", prompt,
    "--model", "claude-haiku-4-5-20251001",  # opus は重いし高い
    "--output-format", "text",
    "--disallowedTools",
        "Bash,Read,Write,Edit,Grep,Glob,WebSearch,WebFetch,Task,TodoWrite,NotebookEdit",
]
subprocess.run(cmd, stdin=subprocess.DEVNULL, ...)
```

### 競合との差別化
- ぴよぴーよ速報 (108 万) と同フォーマット採用、投稿停滞の空白を狙う
- 大人の学び直し TV と差別化: 「真面目 7 : エンタメ 3」
- 過去動画でチンギスハン (3511 回) > 織田信長 (573 回) → 海外題材優先

### 炎上リスク管理
- 台本生成プロンプトに「特定民族・宗教侮辱禁止、現代政治禁止、諸説あり明示」入れる
- 最初の 1 ヶ月は手動チェック後に投稿推奨
- 全自動投稿の前にユーザーへ確認

## ファイルマップ

```
punpun-channel/
├── WAKE_UP.md          # ユーザーが起きた直後に読む
├── QUICKSTART.md       # 30 分で動かす手順
├── README.md           # プロジェクト概要
├── CLAUDE.md           # ← これ
├── docs/
│   ├── REPORT.md       # 留守番作業レポート (経緯)
│   ├── SHOWCASE.md     # 実生成動画スペック
│   ├── 00-vision.md    # ビジョン
│   ├── 01-setup.md     # 詳細セットアップ
│   ├── 02-architecture.md
│   ├── 03-workflow.md
│   ├── 04-competitor-analysis.md
│   └── 05-learnings.md
├── src/                # ソースコード (上記アーキテクチャ参照)
├── config/             # 設定 JSON
├── templates/          # 台本生成プロンプト
├── test_data/          # 手書き短台本 + claude 生成済フル台本
├── scripts/            # 補助コマンド (run.sh/bat, check-env, etc.)
└── assets/             # 素材 (キャラ画像、フォント、BGM)
```

## ユーザーがよく聞きそうな質問への回答テンプレ

**Q: 動画が出来ない**
→ `python scripts/check-env.py` で診断 → 出てきた ❌ をひとつずつ解決

**Q: 声がおかしい**
→ VOICEVOX 起動確認 → `config/voice.json` の speaker.id 確認 → `scripts/pick-voicevox-speaker.py` で再選定

**Q: 画像が出ない**
→ ネット接続確認 → `assets/cache/` にキャッシュされてないか → Wikipedia / いらすとや の URL 直接アクセス可能か

**Q: YouTube に上がらない**
→ `config/youtube-token.json` 存在確認 → `python src/upload/youtube_oauth.py` で再認証

**Q: 毎日自動投稿したい**
→ `scripts/setup-windows-task.ps1` を管理者 PowerShell で実行

**Q: 動画長を変えたい**
→ `templates/script-prompt.md` の章構成を編集 → 次回生成から反映
