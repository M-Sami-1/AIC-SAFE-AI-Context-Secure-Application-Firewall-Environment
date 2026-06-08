param(
    [switch]$FullSetup,
    [switch]$SkipSetup,
    [switch]$SkipOllama,
    [switch]$SkipModelPull
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SetupScript = Join-Path $ProjectRoot "scripts\setup_venv.ps1"
$ReproScript = Join-Path $ProjectRoot "scripts\run_reproducible.ps1"
$RequiredArtifacts = @(
    "dataset\dataset.csv",
    "models\saved\v1_week6\classifier.joblib",
    "models\saved\v1_week6\intent_classifier.joblib",
    "models\saved\v2_week12\classifier.joblib",
    "models\saved\v2_week12\intent_classifier.joblib"
)

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-RequiredArtifacts {
    foreach ($RelativePath in $RequiredArtifacts) {
        if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot $RelativePath))) {
            return $false
        }
    }
    return $true
}

function Test-OllamaReady {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

Push-Location $ProjectRoot
try {
    if (-not $SkipSetup) {
        Write-Step "Setting up Python virtual environment and dependencies"
        & $SetupScript
    }
    elseif (-not (Test-Path -LiteralPath $VenvPython)) {
        throw "Missing .venv. Run without -SkipSetup so dependencies can be installed."
    }

    if ($FullSetup) {
        Write-Step "Running full reproducible workflow: dataset, training, benchmark, and tests"
        & $ReproScript
    }
    elseif (-not (Test-RequiredArtifacts)) {
        Write-Step "Preparing missing dataset and model artifacts"
        & $VenvPython -m dataset.build_dataset
        & $VenvPython -m models.train_tfidf --version v1_week6 --limit 300
        & $VenvPython -m models.train_tfidf --version v2_week12
    }
    else {
        Write-Step "Dataset and model artifacts already exist"
    }

    if (-not $SkipOllama) {
        $Ollama = Get-Command ollama -ErrorAction SilentlyContinue
        if ($Ollama) {
            if (-not (Test-OllamaReady)) {
                Write-Step "Starting Ollama service"
                Start-Process -FilePath $Ollama.Source -ArgumentList "serve" -WindowStyle Hidden
                Start-Sleep -Seconds 5
            }

            if (-not $SkipModelPull) {
                Write-Step "Ensuring Ollama model phi3:mini is available"
                & $Ollama.Source pull phi3:mini
            }

            Write-Step "Warming up Ollama model phi3:mini"
            & $Ollama.Source run phi3:mini "Reply with exactly: AIC-SAFE warmup ready."
        }
        else {
            Write-Warning "Ollama was not found. Install Ollama or run with config.MODEL_SELECTION['mode'] = 'mock'."
        }
    }

    Write-Step "Launching AIC-SAFE"
    & $VenvPython app.py
}
finally {
    Pop-Location
}
