# 👋 おはようございます

寝てる間に動いた結果、**ぷんぷんチャンネルの動画自動化システム、完成しました。**

## TL;DR

✅ **9 分 55 秒の本物の動画 (エリザベート・バートリ) が出来上がっています**
✅ 台本生成 → 音声合成 → 画像取得 → 動画組立 → サムネ作成、全部自動
✅ Claude Max 契約だけで完結 (API キー不要、月 0 円)
✅ コードもドキュメントも全部 commit & push 済

## 🆕 フィードバック (地図/アニメ/口パク) 反映 v2

起きた直後に見てもらって「地図とアニメとキャラの口パクが欲しい」と言われたので、追加実装:

- ✅ **本物の世界/アジア/欧州地図** (Cartopy + Natural Earth)
  - 指定国を緑で塗る。過去動画と同じルック
- ✅ **キャラを斜め向き + 口 3 段階** (口パク用)
  - 音声の RMS エンベロープから自動で口の開き決定
- ✅ **Ken Burns** (ゆっくりズーム)
- ✅ **吹き出しポップイン** (0.35s で登場)
- ✅ **キャラのふわふわ上下** (1.3Hz の自然な揺れ)
- ✅ **シーン頭尾の黒フェード** (繋ぎが自然に)
- ✅ **地図 + 肖像 合成** (`overlay_keyword` で右上に肖像を重ねる)

見られるもの:
- `demo/elizabeth_bathory_full_animated.mp4` ← **これが最新・最高品質** (9:54)
- `demo/elizabeth_bathory_short_animated.mp4` ← 1:17 の動作確認版
- `demo/elizabeth_bathory_demo.mp4` ← 9:55 の v1 版 (静止画、比較用)

**GitHub 直リンク (ブラウザ再生):**
https://github.com/hengchuanyaoyinan-collab/manabi/blob/claude/add-video-creation-gZ3Et/punpun-channel/demo/elizabeth_bathory_full_animated.mp4

## まず何を読むか

1. **`QUICKSTART.md`** ← これだけでまず動かせます (30 分で動画再生まで)
2. **`docs/REPORT.md`** ← 私が何をしたかの全レポート
3. **`docs/SHOWCASE.md`** ← 実際に出来上がった動画のスペック

## 何ができたか早見表

| 項目 | 状態 |
|---|---|
| プロジェクト構造 | ✅ `punpun-channel/` 配下に完全独立 |
| 台本生成 (claude CLI) | ✅ 動作確認済 (エリザベート・バートリ 83 シーン生成済) |
| 音声合成 (VOICEVOX HTTP) | ✅ コード完成 (Windows で起動すれば即動く) |
| 音声合成 (フォールバック) | ✅ open-jtalk で動作確認 |
| 画像取得 (Wikipedia + いらすとや) | ✅ コード完成 |
| 動画組立 (Pillow + FFmpeg) | ✅ **9:55 動画生成成功** |
| サムネ生成 | ✅ 動作確認済 |
| YouTube 自動投稿 | ✅ コード完成 (OAuth 設定が要) |
| Windows タスクスケジューラ登録 | ✅ PowerShell スクリプト用意 |
| 環境診断 | ✅ `scripts/check-env.py` で一発確認 |
| ドキュメント | ✅ 8 つの md (vision, setup, architecture, workflow, learnings, etc.) |
| 競合分析 | ✅ ぴよぴーよ等を分析、戦略明文化 |
| 題材キュー | ✅ 33 個の優先順位付き題材を準備 |

## あなたの作業 (合計 1 時間程度)

1. PC で git clone してブランチ checkout (5 分)
2. Python 環境 + FFmpeg インストール (15 分) - QUICKSTART.md 参照
3. テスト動画再生 (5 分) - すでに 1 本作れる
4. VOICEVOX インストール (15 分) - 声を本物にする
5. YouTube OAuth 設定 (20 分) - 投稿を有効化

## 私からのお願い

**最初の数本は `--test` モードで確認してから手動でアップロード**してください。
全自動投稿は 1 週間品質チェックしてから有効化を推奨します。
炎上は 1 度起きると挽回が大変なので、最初は慎重に。

## 残課題 (Phase 2 として)

これらは「あったらもっと良い」レベル:
- Remotion でアニメーション付与
- 過去動画からぷんぷんキャラ画像を抽出
- カスタム手書き風フォントを配置
- 白地図 SVG / 歴史地図画像を assets に配置
- BGM 配置
- YouTube Analytics API で再生時間最適化

---

がんばってください。チャンネル登録 100 万人、夢じゃないですよ。

— Claude
