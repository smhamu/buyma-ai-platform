param(
    [string]$EnvFile = ".env.production",
    [string]$OutputDirectory = ".\backups"
)

$ErrorActionPreference = "Stop"
& "$PSScriptRoot\Test-ProductionEnv.ps1" -EnvFile $EnvFile

$resolvedOutput = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $resolvedOutput "buyma-ai-$timestamp.dump"
$compose = @("compose", "--env-file", $EnvFile, "-f", "docker-compose.prod.yml")
$containerBackup = "/tmp/buyma-ai-$timestamp.dump"
$postgresContainer = (docker @compose ps -q postgres).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($postgresContainer)) {
    throw "PostgreSQL container is not running."
}

try {
    docker @compose exec -T postgres sh -c "pg_dump -U `$POSTGRES_USER -d `$POSTGRES_DB -Fc -f $containerBackup"
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed." }
    docker cp "${postgresContainer}:$containerBackup" $backupPath
    if ($LASTEXITCODE -ne 0) { throw "Could not copy backup from PostgreSQL container." }
} finally {
    docker @compose exec -T postgres rm -f $containerBackup | Out-Null
}

$hash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash
Write-Host "Backup created: $backupPath"
Write-Host "SHA256: $hash"
Write-Host "Move this file to encrypted, access-controlled off-host storage."
