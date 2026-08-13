param([string]$EnvFile = ".env.production")

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Production environment file not found: $EnvFile"
}

$requiredKeys = @(
    "APP_ENV", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD",
    "DATABASE_URL", "REDIS_PASSWORD", "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND", "SECRET_KEY", "OPENAI_API_KEY"
)
$values = @{}

foreach ($line in Get-Content -LiteralPath $EnvFile) {
    if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
    $key, $value = $line -split '=', 2
    $values[$key.Trim()] = $value.Trim()
}

$errors = @()
foreach ($key in $requiredKeys) {
    if (-not $values.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($values[$key])) {
        $errors += "$key is missing or empty."
    } elseif ($values[$key] -match 'CHANGE_ME') {
        $errors += "$key still contains a placeholder."
    }
}

if ($values["APP_ENV"] -ne "production") { $errors += "APP_ENV must be production." }
if ($values["DATABASE_ECHO"] -ne "false") { $errors += "DATABASE_ECHO must be false." }
if ($values["REGISTRATION_ENABLED"] -ne "false") { $errors += "REGISTRATION_ENABLED must be false." }
if ($values["ENABLE_API_DOCS"] -ne "false") { $errors += "ENABLE_API_DOCS must be false." }
$hstsHeader = if ($values.ContainsKey("HSTS_HEADER")) { $values["HSTS_HEADER"] } else { "" }
if ($hstsHeader -notin @("", "max-age=31536000; includeSubDomains")) {
    $errors += "HSTS_HEADER must be empty or the approved Production value."
}
$secretKey = if ($values.ContainsKey("SECRET_KEY")) { $values["SECRET_KEY"] } else { "" }
if ($secretKey.Length -lt 32) { $errors += "SECRET_KEY must be at least 32 characters." }

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Host "ERROR: $_" -ForegroundColor Red }
    throw "Production environment validation failed. Secret values were not printed."
}

Write-Host "Production environment validation passed. Secret values were not printed."
