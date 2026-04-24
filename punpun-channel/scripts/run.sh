#!/usr/bin/env bash
# よく使うコマンドをまとめた便利スクリプト。
#
# 使い方:
#   ./scripts/run.sh test         # テスト動画を生成 (open-jtalk)
#   ./scripts/run.sh test:vox     # テスト動画 (VOICEVOX)
#   ./scripts/run.sh check        # 環境診断
#   ./scripts/run.sh speakers     # VOICEVOX 話者サンプル生成
#   ./scripts/run.sh script TOPIC # 台本だけ生成
#   ./scripts/run.sh today        # 今日の自動投稿 (本番)

set -euo pipefail
cd "$(dirname "$0")/.."

ACTIVATE=".venv/bin/activate"
if [ ! -f "$ACTIVATE" ]; then
    echo "venv が無いので作成します..."
    python3 -m venv .venv
    . "$ACTIVATE"
    pip install -r requirements.txt
else
    . "$ACTIVATE"
fi

case "${1:-}" in
    test)
        python3 src/orchestrator.py \
            --script test_data/elizabeth_bathory_short.json \
            --test --no-voicevox
        ;;
    test:vox)
        python3 src/orchestrator.py \
            --script test_data/elizabeth_bathory_short.json \
            --test
        ;;
    check)
        python3 scripts/check-env.py
        ;;
    speakers)
        python3 scripts/pick-voicevox-speaker.py
        ;;
    script)
        if [ -z "${2:-}" ]; then
            echo "使い方: ./scripts/run.sh script TOPIC"; exit 1
        fi
        python3 src/generator/script_generator.py "$2"
        ;;
    today)
        python3 src/orchestrator.py
        ;;
    weekly)
        python3 src/analytics.py weekly
        ;;
    best)
        python3 src/analytics.py best
        ;;
    analytics)
        python3 scripts/daily-analytics.py "$@"
        ;;
    review)
        python3 scripts/weekly-review.py "$@"
        ;;
    batch)
        python3 scripts/generate-script-batch.py "${@:2}"
        ;;
    competitors)
        python3 scripts/analyze-competitors.py "${@:2}"
        ;;
    *)
        cat <<EOF
ぷんぷんチャンネル 便利スクリプト

使い方:
  ./scripts/run.sh COMMAND [args]

コマンド:
  test        テスト動画を生成 (open-jtalk)
  test:vox    テスト動画 (VOICEVOX 起動済み前提)
  check       環境診断
  speakers    VOICEVOX 話者サンプル生成
  script TOPIC  指定題材で台本生成
  today       今日の本番動画を生成・投稿 (キューから自動選定)
  weekly      直近1週間のレポート
  best        過去動画の再生数ランキング
EOF
        ;;
esac
