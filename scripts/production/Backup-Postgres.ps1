param(
    [string]$EnvFile = ".env.production",
    [string]$OutputDirectory = ".\backups",
    [string]$ComposeProject = "buyma-ai-production"
)

$ErrorActionPreference = "Stop"
& "$PSScriptRoot\Test-ProductionEnv.ps1" -EnvFile $EnvFile

$resolvedOutput = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $resolvedOutput -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $resolvedOutput "buyma-ai-$timestamp.dump"
if (Test-Path -LiteralPath $backupPath) {
    throw "Refusing to overwrite an existing backup: $backupPath"
}
$compose = @("-p", $ComposeProject, "--env-file", $EnvFile, "-f", "docker-compose.prod.yml")
$containerBackup = "/tmp/buyma-ai-$timestamp.dump"
$postgresContainer = (docker-compose @compose ps -q postgres).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($postgresContainer)) {
    throw "PostgreSQL container is not running."
}

try {
    docker-compose @compose exec -T postgres sh -c "pg_dump -U `$POSTGRES_USER -d `$POSTGRES_DB -Fc -f $containerBackup"
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed." }
    docker cp "${postgresContainer}:$containerBackup" $backupPath
    if ($LASTEXITCODE -ne 0) { throw "Could not copy backup from PostgreSQL container." }
} finally {
    docker exec -u 0 $postgresContainer rm -f $containerBackup | Out-Null
}

Write-Host "Backup created: $backupPath"
Write-Host "Backup size: $((Get-Item -LiteralPath $backupPath).Length) bytes"
Write-Host "Move this file to encrypted, access-controlled off-host storage."
