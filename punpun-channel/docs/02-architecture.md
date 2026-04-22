# システム設計

## 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                 毎日19:00 自動起動                        │
│                 （Windowsタスクスケジューラ）              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ① テーマ選定（Claude Code）                            │
│     ├─ 題材リスト（docs/topic-queue.json）から次を選ぶ  │
│     ├─ 競合が扱ってないもの優先                          │
│     └─ トレンド・季節性を考慮                            │
│                                                          │
│  ② 競合リサーチ（YouTube Data API）                     │
│     ├─ 同テーマの伸びてる動画を取得                      │
│     └─ サムネ・タイトル・タグ傾向を学習                  │
│                                                          │
│  ③ 台本生成（Claude Code）                              │
│     ├─ キャラ設定（ぷんぷん口調）注入                    │
│     ├─ 5章立て、20分相当（約6000字）                     │
│     ├─ シーンごとに [背景タグ] 付与                      │
│     │   例: [地図:モンゴル][肖像:チンギスハン]           │
│     └─ templates/script-template.md に準拠               │
│                                                          │
│  ④ 音声合成（VOICEVOX）                                 │
│     ├─ 台本を1行ずつVOICEVOX Engine APIへ              │
│     ├─ 各セリフのWAV生成                                │
│     └─ 連結してMP3化                                    │
│                                                          │
│  ⑤ 字幕タイミング取得（Whisper）                        │
│     ├─ 生成済み音声をWhisperで解析                       │
│     └─ 各セリフの開始/終了時刻を取得                     │
│                                                          │
│  ⑥ 画像収集                                             │
│     ├─ 肖像画・写真 → Wikipedia Commons API             │
│     ├─ 地図 → 白地図SVG + 色塗り                        │
│     ├─ 感情表現 → いらすとや検索                         │
│     └─ assets/cache/ に保存（再利用）                    │
│                                                          │
│  ⑦ 動画組立（Remotion）                                 │
│     ├─ テンプレート: 背景+吹き出し+ぷんぷん固定           │
│     ├─ 台本の各行に対応するシーンを構築                  │
│     ├─ アニメーション適用（フェード・ズーム等）          │
│     ├─ BGM合成                                          │
│     └─ MP4書き出し（1920x1080、30fps）                  │
│                                                          │
│  ⑧ サムネ生成                                           │
│     ├─ 台本から煽りコピー抽出                            │
│     ├─ 極太フォント + 赤・黒の強い色                     │
│     └─ 1280x720 PNG                                     │
│                                                          │
│  ⑨ メタデータ生成                                       │
│     ├─ タイトル（【〇〇】〇〇のやばすぎる人生 形式）     │
│     ├─ 概要欄（SEO最適化、目次付き）                     │
│     ├─ タグ（15個まで）                                  │
│     └─ チャプター（5章の時刻）                           │
│                                                          │
│  ⑩ YouTubeアップロード                                  │
│     ├─ YouTube Data API v3                              │
│     ├─ 19:00公開予約                                    │
│     ├─ 終了画面・カード設定                              │
│     └─ プレイリスト自動追加                              │
│                                                          │
│  ⑪ レポート（翌朝）                                     │
│     ├─ 前日投稿動画の成績                                │
│     ├─ 週次/月次の傾向                                   │
│     └─ 改善提案                                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## データフロー

```
topic-queue.json
      ↓
   ┌──────┐
   │ 題材 │ "エリザベート・バートリ"
   └──────┘
      ↓
  Claude Code
      ↓
   ┌─────────────────┐
   │ script.md       │
   │ [OP][背景:城]   │
   │ どうもこんにちは…│
   │ [Ch1][肖像:本人]│
   │ ...             │
   └─────────────────┘
      ↓
  VOICEVOX Engine
      ↓
   narration.mp3
      ↓
   Whisper
      ↓
   timings.json
      ↓
  Image Collector
      ↓
   images/*.png
      ↓
   Remotion
      ↓
   video.mp4
      ↓
  YouTube API
      ↓
   📺 公開
```

## 主要コンポーネント

### src/generator/
台本生成と題材管理
- `topic-selector.ts` - 題材選定ロジック
- `script-generator.ts` - Claude Code呼び出し
- `prompt-templates/` - プロンプトテンプレート

### src/voice/
音声合成
- `voicevox-client.ts` - VOICEVOX Engine API クライアント
- `audio-mixer.ts` - 音声連結・BGMミックス

### src/video/
動画組立（Remotion）
- `compositions/` - Remotionコンポジション
  - `main-video.tsx` - メイン動画
  - `scene.tsx` - 1シーン
  - `speech-bubble.tsx` - 吹き出し
  - `punpun-character.tsx` - ぷんぷん
- `utils/` - 画像取得等

### src/upload/
YouTube投稿
- `youtube-uploader.ts` - API呼び出し
- `metadata-generator.ts` - タイトル・概要欄生成
- `thumbnail-generator.ts` - サムネ生成

## 設定ファイル

### config/channel.json
チャンネル全体の設定
```json
{
  "channelName": "ぷんぷんの世事見聞録",
  "handle": "@ororonchi-sv6by",
  "videoLength": 1200,
  "uploadTime": "19:00",
  "uploadFrequency": "daily",
  "language": "ja"
}
```

### config/voice.json
音声設定
```json
{
  "engine": "voicevox",
  "speaker": 8,
  "speed": 1.05,
  "pitch": 0.02,
  "volume": 1.0
}
```

### config/style.json
映像スタイル
```json
{
  "resolution": "1920x1080",
  "fps": 30,
  "characterPosition": "bottom-right",
  "bubbleStyle": "handwritten",
  "fontFamily": "あずきフォント"
}
```

### config/topic-queue.json
題材キュー（次回以降の投稿予定）
```json
{
  "queue": [
    { "topic": "エリザベート・バートリ", "scheduled": "2026-04-23" },
    { "topic": "カリグラ帝", "scheduled": "2026-04-24" },
    ...
  ],
  "posted": [...]
}
```

## 実行モード

### 1. テスト実行
```bash
npm run generate -- --topic "エリザベート・バートリ" --test
```
- 動画は生成するが、アップロードしない
- output/test/ に保存

### 2. 本番実行
```bash
npm run generate -- --auto
```
- キューから次の題材を取得
- 生成〜投稿まで実行

### 3. 手動指定
```bash
npm run generate -- --topic "カリグラ帝" --publish
```

## 技術的な選択理由

### なぜRemotion?
- Reactコンポーネントで動画を作れる（プログラマブル）
- テンプレート化しやすい
- 無料
- MP4出力可能

### なぜVOICEVOX?
- 完全無料・ローカル動作
- 商用利用可（各キャラの規約要確認）
- 日本語品質◎
- Engine APIで自動化しやすい

### なぜClaude Code (Max契約)?
- ユーザー既に契約済み
- 追加料金ゼロ
- 20分の台本を高品質に生成可能

### なぜPython + Node.js 併用?
- 動画生成 → Remotion（Node.js必須）
- 画像処理・API呼び出し → Python得意
- 役割分担で両方使う

## セキュリティ・運用上の注意

- YouTubeの認証トークンは `.env` に入れる（Gitにコミットしない）
- `.env.example` だけコミット
- アップロード前に必ずプレビュー確認（最初の1ヶ月）
- 炎上リスクのある題材は手動チェック
