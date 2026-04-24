# BGM (Background Music) ライブラリ

このフォルダに BGM ファイル (mp3/wav) を配置すると、自動で章別にミックスされます。

## ファイル命名規則

`<任意名>_<カテゴリ>_<任意>.mp3`

カテゴリ (必須) — ファイル名にキーワードとして含める:

| カテゴリ | 用途 | 章 |
|---|---|---|
| `op` | オープニング (緊張感) | 0 |
| `peaceful` | 生い立ち (穏やか) | 1 |
| `drama` | 転機 (テンポ UP) | 2 |
| `epic` | 全盛期 (オーケストラ) | 3 |
| `dark` | 狂気 (重い) | 4 |
| `sad` | 最期 (静か) | 5 |
| `uplift` | まとめ (前向き) | 6 |

## 例

```
bgm_op_01.mp3       ← OP 用
peaceful_pianoforte.mp3  ← Chapter 1 用
drama_rising.mp3    ← Chapter 2 用
```

## おすすめ入手先 (全て商用可、クレジット要 / 不要はサイトで確認)

- **DOVA-SYNDROME** https://dova-s.jp/ (日本の定番、クレジット不要)
- **魔王魂** https://maou.audio/ (エモい曲多め、商用 OK)
- **甘茶の音楽工房** https://amachamusic.chagasi.com/ (穏やか系)
- **YouTube オーディオライブラリ** (Studio から DL、YT 内で完全自由)
- **Pixabay Music** https://pixabay.com/music/ (CC0)

## 推奨構成 (最小セット)

各カテゴリ 1〜2 曲で十分動きます。合計 7〜14 曲。

`op_1.mp3`, `peaceful_1.mp3`, `drama_1.mp3`, `epic_1.mp3`, `dark_1.mp3`, `sad_1.mp3`, `uplift_1.mp3`

## 動作確認

BGM 配置後、通常のパイプライン実行で自動検出・ミックスされます:
```bash
python src/orchestrator.py --script test_data/カリグラ帝.json --test
```
ログに `BGM/SE mixed into narration` が出れば成功。
