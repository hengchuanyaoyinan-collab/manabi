@echo off
REM =====================================================
REM ぷんぷんの世事見聞録 - 初回実行 (ワンクリック)
REM =====================================================
REM このファイルをダブルクリックするだけで:
REM  1. Python 環境 (venv) 準備
REM  2. 依存インストール
REM  3. テスト動画生成
REM  4. 出来た動画を開く
REM =====================================================

chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ============================================================
echo   ぷんぷんの世事見聞録 - 初回セットアップ + テスト動画生成
echo ============================================================
echo.

REM --- Python 確認 ---
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python が見つかりません
    echo https://www.python.org/downloads/ からインストールして、
    echo 「Add Python to PATH」にチェックを入れてください。
    pause
    exit /b 1
)

REM --- FFmpeg 確認 ---
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] FFmpeg が見つかりません
    echo PowerShell を管理者で開いて以下を実行:
    echo   winget install Gyan.FFmpeg
    echo その後 PowerShell を再起動してからこの .bat を実行してください。
    pause
    exit /b 1
)

REM --- venv 作成 ---
if not exist ".venv\Scripts\activate.bat" (
    echo [1/4] Python 仮想環境を作成中...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] venv 作成失敗
        pause
        exit /b 1
    )
)

REM --- 依存インストール ---
echo [2/4] 依存パッケージをインストール中 (初回は 5-10 分)...
call .venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 依存インストール失敗
    echo requirements.txt の内容を確認してください
    pause
    exit /b 1
)

REM --- テスト動画生成 ---
echo [3/4] テスト動画を生成中 (10-15 分)...
python src\orchestrator.py --script test_data\chinghis_khan_v4.json --test --no-voicevox
if %errorlevel% neq 0 (
    echo [ERROR] 動画生成失敗
    pause
    exit /b 1
)

REM --- 動画を開く ---
echo [4/4] 完成した動画を開きます...
for /f "delims=" %%D in ('dir /b /od output\test 2^>nul') do set LATEST=%%D
if defined LATEST (
    if exist "output\test\%LATEST%\video.mp4" (
        start "" "output\test\%LATEST%\video.mp4"
        echo.
        echo ✅ 成功! 動画が開きました:
        echo    output\test\%LATEST%\video.mp4
    ) else (
        echo [ERROR] video.mp4 が見つかりません
    )
) else (
    echo [ERROR] output\test フォルダが空です
)

echo.
echo ============================================================
echo   完了。品質が気になる場合は SETUP-WINDOWS.md を参照。
echo ============================================================
pause
