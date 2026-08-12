param(
    [Parameter(Mandatory = $true)][string]$BackupFile,
    [string]$EnvFile = ".env.production"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $BackupFile)) { throw "Backup not found: $BackupFile" }
& "$PSScriptRoot\Test-ProductionEnv.ps1" -EnvFile $EnvFile

$restoreDb = "buyma_restore_$((Get-Date).ToString('yyyyMMddHHmmss'))"
$compose = @("compose", "--env-file", $EnvFile, "-f", "docker-compose.prod.yml")
$containerBackup = "/tmp/$restoreDb.dump"
$postgresContainer = (docker @compose ps -q postgres).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($postgresContainer)) {
    throw "PostgreSQL container is not running."
}

try {
    docker cp ([IO.Path]::GetFullPath($BackupFile)) "${postgresContainer}:$containerBackup"
    if ($LASTEXITCODE -ne 0) { throw "Could not copy backup into PostgreSQL container." }
    docker @compose exec -T postgres sh -c "createdb -U `$POSTGRES_USER $restoreDb"
    if ($LASTEXITCODE -ne 0) { throw "Could not create disposable restore database." }

    docker @compose exec -T postgres sh -c "pg_restore -U `$POSTGRES_USER -d $restoreDb --no-owner --no-privileges $containerBackup"
    if ($LASTEXITCODE -ne 0) { throw "Restore failed." }

    docker @compose exec -T postgres sh -c "psql -U `$POSTGRES_USER -d $restoreDb -tAc 'SELECT COUNT(*) FROM alembic_version'"
    if ($LASTEXITCODE -ne 0) { throw "Restored database verification failed." }
    Write-Host "Restore drill passed using disposable database $restoreDb."
} finally {
    docker @compose exec -T postgres sh -c "dropdb -U `$POSTGRES_USER --if-exists $restoreDb" | Out-Null
    docker @compose exec -T postgres rm -f $containerBackup | Out-Null
}
