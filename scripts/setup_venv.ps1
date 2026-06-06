$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Python) {
        throw "Python was not found on PATH. Install Python 3.11, then rerun this script."
    }
    & $Python.Source -m venv (Join-Path $ProjectRoot ".venv")
}

& $VenvPython -m pip install --upgrade pip==24.1.2
& $VenvPython -m pip install -r $Requirements
& $VenvPython -m pip freeze | Out-File -Encoding utf8 (Join-Path $ProjectRoot "requirements.lock.txt")

Write-Host "Project virtual environment ready: $VenvPython"
