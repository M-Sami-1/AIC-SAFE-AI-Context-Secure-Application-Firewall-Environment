$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LogDir = Join-Path $ProjectRoot "logs"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$TranscriptPath = Join-Path $LogDir "reproducible_run_$Timestamp.log"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Missing project virtual environment. Run scripts/setup_venv.ps1 first."
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Start-Transcript -Path $TranscriptPath | Out-Null
try {
    Push-Location $ProjectRoot
    try {
        & $VenvPython -m dataset.build_dataset
        & $VenvPython -m models.train_tfidf --version v1_week6 --limit 300
        & $VenvPython -m models.train_tfidf --version v2_week12
        & $VenvPython -m evaluation.benchmark
        & $VenvPython -m pytest
    }
    finally {
        Pop-Location
    }
}
finally {
    Stop-Transcript | Out-Null
}
