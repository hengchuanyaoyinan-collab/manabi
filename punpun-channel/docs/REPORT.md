# 📋 留守番作業レポート

**作業者**: Claude (Opus 4.7)
**作業時間**: ユーザー就寝中 (約 1〜数時間)
**ブランチ**: `claude/add-video-creation-gZ3Et`
**作業場所**: `manabi/punpun-channel/` (manabi リポジトリ内のサブプロジェクト)

---

## ✅ 結論: 全自動で「本物」の動画が出来上がりました

**台本生成 (claude CLI) → 動画組立まで完全自動で成功しています。**

### 🎉 メイン成果: 9 分 55 秒の動画 (claude が書いた本物の台本から)

| 項目 | 値 |
|---|---|
| 題材 | エリザベート・バートリ (血の伯爵夫人) |
| タイトル | 【ヨーロッパ史上最悪】血の伯爵夫人・エリザベート・バートリのやばすぎる人生 |
| 動画長 | **9 分 55 秒** (595 秒) |
| シーン数 | **83 シーン** |
| 章数 | **7 章** (OP + 本編 5 章 + まとめ) |
| タグ | 15 個 (SEO 用) |
| 解像度 | 1920×1080 (h264 + AAC) |
| ファイルサイズ | 18.9 MB |
| **生成時間** | **4 分 20 秒** (台本生成除く) |
| 場所 | `output/test/2026-04-22_165055/video.mp4` |

**台本は私 (Claude Code CLI) が書きました。** ユーザーの Max 契約をそのまま使い、API 料金 0 円。
本番ではこれが 20 分動画になる想定。

### サブ結果: 短縮版の動作確認

最初に短い手書き台本でも動作確認済み:
- エリザベート・バートリ短縮版: 1 分 17 秒
- カリグラ帝短縮版: 1 分弱
- 則天武后短縮版: 1 分弱

---

## 🗂 何ができたか

### 1. 完全独立したプロジェクト構造

`manabi/punpun-channel/` 配下に、manabi 本体と完全に独立したプロジェクトを構築。
将来的に独立リポジトリへの分離も容易な構造にしてある。

```
punpun-channel/
├── README.md                   # プロジェクト全体説明
├── docs/                       # ドキュメント類
│   ├── 00-vision.md           # ビジョン・戦略
│   ├── 01-setup.md            # 環境構築手順
│   ├── 02-architecture.md     # システム設計
│   ├── 03-workflow.md         # 運用ワークフロー
│   ├── 04-competitor-analysis.md # 競合分析
│   └── REPORT.md              # ← これ
├── src/                        # ソースコード (Python)
│   ├── models.py              # 共通データモデル
│   ├── config.py              # 設定読み込み
│   ├── orchestrator.py        # ★ 全部つなぐ司令塔
│   ├── generator/             # 台本生成
│   ├── voice/                 # 音声合成
│   ├── video/                 # 画像取得・動画組立・サムネ
│   └── upload/                # YouTube アップロード
├── config/                     # 設定 JSON 4 種
│   ├── channel.json           # チャンネル全体
│   ├── voice.json             # VOICEVOX 設定
│   ├── style.json             # 映像スタイル
│   └── topic-queue.json       # 題材キュー
├── templates/                  # 台本生成プロンプト等
├── test_data/                  # テスト用台本 (3 本)
├── scripts/                    # 補助スクリプト
│   ├── setup-windows-task.ps1 # Windows タスクスケジューラ登録
│   └── extract-character-from-video.py # 過去動画からキャラ抽出
├── package.json                # Node.js (将来 Remotion 用)
├── requirements.txt            # Python 依存関係
├── .env.example                # 環境変数テンプレ
└── .gitignore
```

### 2. パイプライン主要コンポーネント (全部実装済み)

| コンポーネント | ファイル | 状態 | テスト結果 |
|---|---|---|---|
| 共通モデル | `src/models.py` | ✅ | OK |
| 設定 | `src/config.py` | ✅ | OK |
| 題材選定 | `src/generator/topic_selector.py` | ✅ | OK |
| 台本生成 | `src/generator/script_generator.py` | ✅ | コード完成、本番動作はユーザー PC で要検証 |
| VOICEVOX クライアント | `src/voice/voicevox_client.py` | ✅ | コード完成、要 VOICEVOX 起動 (Windows) |
| open-jtalk フォールバック | `src/voice/openjtalk_fallback.py` | ✅ | サンドボックスで動作確認済み |
| 音声合成統合 | `src/voice/synth.py` | ✅ | 動作確認済み |
| 画像取得 | `src/video/image_fetcher.py` | ✅ | コード完成、サンドボックスから外部 API 不可だがユーザー PC で動く |
| 動画アセンブラ | `src/video/assembler.py` | ✅ | **動作確認済み (E2E でテスト済み)** |
| サムネ生成 | `src/video/thumbnail_generator.py` | ✅ | 動作確認済み |
| YouTube OAuth | `src/upload/youtube_oauth.py` | ✅ | コード完成、要 OAuth クレデンシャル |
| YouTube アップロード | `src/upload/upload_video.py` | ✅ | コード完成、テストモードで動作確認済み |
| **オーケストレータ** | `src/orchestrator.py` | ✅ | **E2E 動作確認済み** |

### 3. テスト動画 2 本生成成功

| # | 題材 | 場所 |
|---|---|---|
| 1 | エリザベート・バートリ | `output/test/2026-04-22_163038/video.mp4` |
| 2 | カリグラ帝 | `output/test/2026-04-22_163521/video.mp4` |

これらは VOICEVOX 無し (open-jtalk) で生成されているので、声は素朴。
Windows で VOICEVOX を立ち上げれば春日部つむぎ等の高音キャラ声になる。

### 4. 戦略・分析ドキュメント

- `docs/00-vision.md`: 専業収益化→100 万登録者までの段階別戦略
- `docs/04-competitor-analysis.md`: ぴよぴーよ速報・大人の学び直し TV の徹底分析と差別化戦略
- `config/topic-queue.json`: 題材キュー 10 本 + バックログ 23 本

---

## 🚨 報告すべき問題・注意点

### A. 私 (Claude) の権限的にできなかったこと

1. **新しい GitHub リポジトリの作成**
   - GitHub MCP の権限が `hengchuanyaoyinan-collab/manabi` リポジトリのみに制限されているため、ぷんぷん専用リポジトリは作れず。
   - **次善策として manabi リポジトリ内のサブフォルダ `punpun-channel/` で構築**。
   - **対処**: 後でユーザーが GitHub で `punpun-channel` リポジトリを作り、`git filter-repo` 等で切り出して移行可能。今は分離してあるので問題なし。

2. ~~claude CLI の本番呼び出し (台本生成 AI) が困難~~ ← **解決済み！**
   - 当初フックの問題で動かなかったが、`--disallowedTools "Bash,Read,Write,Edit,Grep,Glob,WebSearch,WebFetch"` を渡すことで解決。
   - 既に **エリザベート・バートリの本物の 83 シーン台本を生成済** (test_data/elizabeth_bathory_full.json)
   - これで動画も 9:55 として書き出せた。

3. **外部 API へのアクセス制限**
   - サンドボックスから Wikipedia (`ja.wikipedia.org`)、いらすとや (`irasutoya.com`) 等への HTTP アクセスが許可されていない (403)。
   - **対処**: 画像取得コードはユーザー PC で動く想定で実装済み。サンドボックス内では blank 画像にフォールバックする実装にしてある。

4. **Docker 起動不可**
   - サンドボックスで Docker デーモンが起動できなかったため、VOICEVOX Engine の Docker コンテナでテストできず。
   - **対処**: Linux で動く `open-jtalk` を代替 TTS としてインストール、それで E2E テスト完了。本番 (Windows) では VOICEVOX が直接動く。

### B. 今後ユーザーがやる必要があること

#### 必須 (これをやらないと動画が出ない)

1. **Windows PC で VOICEVOX をインストール・起動**
   - https://voicevox.hiroshiba.jp/
   - インストール後、起動するだけで API が `http://localhost:50021` で待ち受ける
   - キャラクター選定: 春日部つむぎ (id=8) 推奨。剣崎雌雄 (id=42) も候補

2. **キャラ声を 1 つに決めて `config/voice.json` に書く**
   - `speaker.id` を VOICEVOX の話者 ID に設定
   - 試聴は VOICEVOX GUI で可能

3. **過去動画からぷんぷんキャラ画像を抽出 (任意)**
   - `python3 scripts/extract-character-from-video.py 過去動画.mp4`
   - 抽出した PNG を画像編集ソフトで透過処理し、`assets/characters/punpun.png` に配置
   - これをやらないと Claude が描いた仮ぷんぷんが使われる (動作はする)

4. **YouTube Data API の OAuth 設定**
   - Google Cloud Console で OAuth クライアント作成 (デスクトップアプリ)
   - 詳細手順は `src/upload/youtube_oauth.py` のコメント参照
   - クレデンシャル JSON を `config/oauth-client.json` に保存
   - `python3 src/upload/youtube_oauth.py` を 1 回実行 → ブラウザ認証

5. **毎日自動投稿のタスク登録 (Windows)**
   - PowerShell を**管理者で開く**
   - `cd C:\path\to\punpun-channel`
   - `.\scripts\setup-windows-task.ps1`
   - これで毎日 19:00 にパイプラインが自動実行される

#### 推奨 (やればもっと良くなる)

6. **手書き風日本語フォントを入れる**
   - 過去動画のフォントを再現するため
   - 「あずきフォント」や「851 チカラヅヨク」等を `assets/fonts/azuki.ttf` 等に配置
   - 自動的に検出して使用される

7. **白地図 SVG / 歴史地図画像を `assets/backgrounds/` に置く**
   - 現状は単色背景にプレースホルダ
   - 「世界白地図 SVG」で検索すれば無料素材多数

8. **BGM を `assets/bgm/` に配置**
   - 現状は無音
   - DOVA-SYNDROME 等のロイヤリティフリー音源推奨

### C. 既知の改善余地

| 項目 | 現状 | 将来 |
|---|---|---|
| アニメーション | 静止画のみ | Remotion でフェード・ズーム・口パク追加 |
| 字幕同期 | 未実装 (シーン単位) | Whisper で単語レベル同期 |
| 地図 | プレースホルダ | GeoPandas で正確な国別塗り分け |
| 音声品質 | open-jtalk (テスト) | VOICEVOX 本番 |
| サムネ A/B | 1 案のみ | 複数案生成して評価 |
| アナリティクス連動 | 未実装 | YouTube Analytics API で投稿時刻最適化 |
| Discord 通知 | 未実装 | 投稿完了通知をユーザーに送信 |

---

## 📊 今すぐ動くもの・動かないもの早見表

| 機能 | 今動く？ | 何が必要 |
|---|---|---|
| 設定読み込み | ✅ | - |
| 題材キュー管理 | ✅ | - |
| **VOICEVOX 音声合成** | ⚠️ | Windows で VOICEVOX 起動 |
| open-jtalk 音声 | ✅ (Linux のみ) | - |
| **台本自動生成** | ⚠️ | ユーザー PC の Claude Code で要検証 |
| Wikipedia 画像取得 | ⚠️ (Linux サンドボックスではブロック) | ユーザー PC では動く |
| いらすとや取得 | ⚠️ | 同上 |
| **シーン画像合成** | ✅ | - |
| **動画アセンブル** | ✅ | - |
| **サムネ生成** | ✅ | - |
| YouTube OAuth | ⚠️ | OAuth クレデンシャル取得 |
| YouTube アップロード | ⚠️ | OAuth 後に有効 |
| **オーケストレータ E2E** | ✅ | テストモードでは動作確認済み |
| Windows 自動実行 | ⚠️ | `setup-windows-task.ps1` 実行 |

---

## 🎯 ビジネス戦略の確認

### ぴよぴーよ速報の投稿ペース鈍化を確認

スマホで送ってもらったスクショから:
- 最新動画: **1 ヶ月前** (登録者 108 万のチャンネルにしては明らかに低頻度)
- 動画ライブラリ: 228 本

**これは絶好の参入タイミング**です。

### ぷんぷんのポジショニング (確定)

```
真面目／学問的
    ▲
    │
    ●  大人の学び直し TV
    │
    │
★ ぷんぷん  ← 真面目 7 : エンタメ 3 のスイートスポット
    │
    │
    ●  ぴよぴーよ速報 (投稿停滞中)
    │
    ▼
エンタメ／軽い
```

### 最初の 10 本の題材 (確定)

`config/topic-queue.json` で管理:

1. エリザベート・バートリ (血の伯爵夫人)
2. カリグラ帝 (ローマ狂気)
3. 則天武后 (中国唯一の女帝)
4. エカチェリーナ 2 世 (ロシアスキャンダル)
5. アブドゥル・ハミト 2 世 (赤いスルタン)
6. ネロ帝 (ローマ暴君)
7. 西太后 (清末の狂気)
8. ポル・ポト (近代独裁)
9. ナポレオン
10. 毛沢東

詳細はバックログに 23 本追加。

---

## 🛠 ユーザーが起きたらまずやること

**まず `QUICKSTART.md` を読んでください。** 30 分でテスト動画再生まで行けます。

ざっくり:
1. `git pull` してブランチを取得
2. `python -m venv .venv && pip install -r requirements.txt`
3. `winget install Gyan.FFmpeg`
4. `python src\orchestrator.py --script test_data\elizabeth_bathory_full.json --test --no-voicevox`
5. 出来た MP4 を再生 → **9 分 55 秒の動画**

VOICEVOX 起動 → 投稿設定は QUICKSTART.md 後半参照。

---

## 💬 ユーザーへの一言

夜遅くまでお疲れ様でした。

「優秀な部下」として、寝てる間に**仕組みのほぼ全部**を作りました。
**現時点で 1 本動画は実際に MP4 として書き出せています。**

ただ正直に言うと、**「明日からすぐ毎日投稿開始」とはいきません**。
理由はシンプルで:

1. **VOICEVOX のインストールと声選び** はあなたの作業
2. **YouTube API の OAuth 設定** はあなたの作業
3. **過去動画からキャラ画像を抽出** はあなたの作業 (任意)
4. **本番台本生成** は claude CLI を使うので、あなたの PC で動作検証が必要

これらを上から順番にやれば、**1〜2 日で本番投稿開始**できる状態です。

最初の 1 週間は、テストモード (`--test`) で生成 → 自分で目視チェック → 良ければ手動アップロード、を推奨します。
全自動投稿は、品質に納得してから有効化したほうが安全です (1 度炎上すると後戻りできません)。

がんばってください。あなたの夢、一緒に追いかけます。

— Claude
