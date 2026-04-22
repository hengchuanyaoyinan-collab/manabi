# Windows タスクスケジューラ登録 PowerShell スクリプト
#
# 毎日 19:00 にぷんぷんパイプラインを実行するタスクを登録する。
#
# 使い方 (PowerShell を管理者で開いて実行):
#   .\setup-windows-task.ps1
#
# 解除 (タスクの削除):
#   .\setup-windows-task.ps1 -Uninstall

[CmdletBinding()]
param(
    [switch]$Uninstall,
    [string]$ProjectDir = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Time = "19:00",
    [string]$TaskName = "PunpunDailyVideo"
)

$ErrorActionPreference = "Stop"

if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ タスク '$TaskName' を削除しました"
    } else {
        Write-Host "ℹ️  タスク '$TaskName' は登録されていません"
    }
    exit
}

# Python を探す
$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    Write-Error "Python が見つかりません。先に Python をインストールしてください: https://www.python.org/"
}

# venv があれば優先
$venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (Test-Path $venvPython) { $python = $venvPython }

# ログディレクトリ
$logDir = Join-Path $ProjectDir "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

# アクション (orchestrator を実行)
$logFile = Join-Path $logDir "task_run.log"
$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument "src/orchestrator.py" `
    -WorkingDirectory $ProjectDir

# トリガー (毎日指定時刻)
$trigger = New-ScheduledTaskTrigger -Daily -At $Time

# 設定
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# 既存があれば上書き
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "ぷんぷんの世事見聞録 自動投稿パイプライン" | Out-Null

Write-Host "✅ タスク '$TaskName' を登録しました"
Write-Host "   実行時刻: 毎日 $Time"
Write-Host "   Python: $python"
Write-Host "   作業ディレクトリ: $ProjectDir"
Write-Host ""
Write-Host "確認: タスクスケジューラ (taskschd.msc) で確認できます"
Write-Host "ログ: $logFile"
