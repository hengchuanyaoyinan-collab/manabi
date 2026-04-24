# 効果音 (SE) ライブラリ

このフォルダに SE ファイル (mp3/wav) を配置すると、
自動で章切替・衝撃シーンに配置されます。

## ファイル命名規則

ファイル名にキーワードを含める:

| キーワード | 用途 | タイミング |
|---|---|---|
| `chapter` | 章切替 | 章の頭 |
| `shock` | 衝撃シーン | emotion=shock のシーン |
| `flash` | フラッシュ演出 | 瞬間強調 |
| `intro` | 登場音 | OP の入り |

## 例

```
chapter_transition.mp3  ← 章切替
shock_gasp.wav          ← 驚き
flash_1.mp3             ← フラッシュ
intro_zoom.mp3          ← OP
```

## おすすめ入手先 (商用可)

- **効果音ラボ** https://soundeffect-lab.info/ (日本の定番、完全無料)
- **OtoLogic** https://otologic.jp/ (高品質 SE、クレジット要)
- **On-Jin 〜音人〜** https://on-jin.com/ (日本の効果音)
- **Pixabay Sounds** https://pixabay.com/sound-effects/ (CC0)

## 推奨セット (最小)

- `chapter_1.mp3` (章切替: 柔らかいピコン or ドン)
- `shock_1.mp3` (驚き: ジャーン or ガーン)
- `flash_1.mp3` (フラッシュ: キラーン or ヒュッ)

合計 3〜5 個で十分。

## 動作

SE 配置は `src/audio/mixer.py` の `plan_se_placements()` が台本から
自動決定します。emotion=shock のシーン頭に `shock_*.mp3` を挿入、
章切替で `chapter_*.mp3` を挿入。
