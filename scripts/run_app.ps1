$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Missing project virtual environment. Run scripts/setup_venv.ps1 first."
}

Push-Location $ProjectRoot
try {
    & $VenvPython -m streamlit run app.py
}
finally {
    Pop-Location
}
