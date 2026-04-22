@echo off
REM Windows 用便利スクリプト
REM 使い方: scripts\run.bat test

cd /d "%~dp0\.."

if not exist .venv\Scripts\activate.bat (
    echo venv が無いので作成します...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

if "%1"=="" goto help
if "%1"=="test" (
    python src\orchestrator.py --script test_data\elizabeth_bathory_short.json --test --no-voicevox
    goto end
)
if "%1"=="test:vox" (
    python src\orchestrator.py --script test_data\elizabeth_bathory_short.json --test
    goto end
)
if "%1"=="check" (
    python scripts\check-env.py
    goto end
)
if "%1"=="speakers" (
    python scripts\pick-voicevox-speaker.py
    goto end
)
if "%1"=="script" (
    if "%2"=="" (
        echo 使い方: scripts\run.bat script TOPIC
        exit /b 1
    )
    python src\generator\script_generator.py "%2"
    goto end
)
if "%1"=="today" (
    python src\orchestrator.py
    goto end
)
if "%1"=="weekly" (
    python src\analytics.py weekly
    goto end
)
if "%1"=="best" (
    python src\analytics.py best
    goto end
)

:help
echo ぷんぷんチャンネル 便利スクリプト
echo.
echo 使い方: scripts\run.bat COMMAND [args]
echo.
echo コマンド:
echo   test        テスト動画を生成 (open-jtalk)
echo   test:vox    テスト動画 (VOICEVOX 起動済み前提)
echo   check       環境診断
echo   speakers    VOICEVOX 話者サンプル生成
echo   script TOPIC  指定題材で台本生成
echo   today       今日の本番動画を生成・投稿
echo   weekly      直近1週間のレポート
echo   best        過去動画の再生数ランキング

:end
