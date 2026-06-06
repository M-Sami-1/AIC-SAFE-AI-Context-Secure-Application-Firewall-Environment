$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ProjectPython = Join-Path $ProjectRoot ".python311\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    if (Test-Path -LiteralPath $ProjectPython) {
        $PythonExe = $ProjectPython
    }
    else {
        $Python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $Python) {
            throw "Python was not found. Install Python 3.11 or place project-local Python at .python311\python.exe."
        }
        $PythonExe = $Python.Source
    }
    & $PythonExe -m venv (Join-Path $ProjectRoot ".venv")
}

& $VenvPython -m pip install --upgrade pip==24.1.2
& $VenvPython -m pip install -r $Requirements
& $VenvPython -m pip freeze | Out-File -Encoding utf8 (Join-Path $ProjectRoot "requirements.lock.txt")

Write-Host "Project virtual environment ready: $VenvPython"
