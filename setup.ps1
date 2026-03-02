<#
Setup script for Station Engine project
Works on Windows
#>

# --- Check Python installation ---
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python is not installed. Please install Python 3.8+ and rerun this script." -ForegroundColor Red
    exit 1
}

# --- Install pip packages ---
Write-Host "Installing required Python packages..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r requirements.txt

# --- Create .env file ---
$envFile = Join-Path -Path $PSScriptRoot -ChildPath ".env"
$exampleEnv = Join-Path -Path $PSScriptRoot -ChildPath ".env.example"

if (-not (Test-Path $envFile)) {
    if (Test-Path $exampleEnv) {
        Copy-Item -Path $exampleEnv -Destination $envFile
        Write-Host ".env file created from .env.example" -ForegroundColor Green
        Write-Host "Please edit .env and add your database credentials." -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: .env.example file not found. Please create one with required variables." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host ".env file already exists. Skipping creation." -ForegroundColor Green
}

# --- Verify .env variables ---
$requiredVars = @("DB_HOST","DB_USER","DB_PASSWORD","DB_NAME")
$missing = @()

foreach ($var in $requiredVars) {
    $value = (Get-Content $envFile | Where-Object { $_ -match "^$var=" })
    if (-not $value) { $missing += $var }
}

if ($missing.Count -gt 0) {
    Write-Host "WARNING: The following environment variables are missing in .env:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  $_" }
} else {
    Write-Host "All required environment variables are present in .env" -ForegroundColor Green
}

Write-Host "`nSetup complete. You can now run:" -ForegroundColor Cyan
Write-Host "python app.py"
