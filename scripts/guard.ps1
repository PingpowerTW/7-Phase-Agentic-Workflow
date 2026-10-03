<#
.SYNOPSIS
    System 1 決策門禁快捷執行腳本 (相容 TypeSafe Jev / Ollaya 等開放 /v1/systemone 協議規範)
.DESCRIPTION
    調用 .venv/Scripts/python.exe 執行 scripts/local_guard.py
    支援自動檢測 git diff、檔案或代碼字串，具備自動離線降級 (Static Fallback)
.EXAMPLE
    .\scripts\guard.ps1
    .\scripts\guard.ps1 -Code "export function add(a, b) { return a + b; }"
    .\scripts\guard.ps1 -File "src/index.ts"
#>
param(
    [switch]$Git,
    [string]$Code,
    [string]$File
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$guardPy = Join-Path $scriptDir "local_guard.py"

$passArgs = @()
if ($Code) {
    $passArgs += "--code", $Code
} elseif ($File) {
    $passArgs += "--file", $File
} else {
    $passArgs += "--git"
}

& $pythonExe $guardPy @passArgs
exit $LASTEXITCODE
