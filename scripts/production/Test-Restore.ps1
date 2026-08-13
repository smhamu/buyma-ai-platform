param(
    [Parameter(Mandatory = $true)][string]$BackupFile,
    [string]$EnvFile = ".env.production",
    [string]$ComposeProject = "buyma-ai-production"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $BackupFile)) { throw "Backup not found: $BackupFile" }
& "$PSScriptRoot\Test-ProductionEnv.ps1" -EnvFile $EnvFile

$envValues = @{}
foreach ($line in Get-Content -LiteralPath $EnvFile) {
    if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
    $key, $value = $line -split '=', 2
    $envValues[$key.Trim()] = $value.Trim()
}
$dbUser = $envValues["POSTGRES_USER"]
$productionDb = $envValues["POSTGRES_DB"]

$restoreDb = "buyma_restore_$((Get-Date).ToString('yyyyMMddHHmmss'))_$([Guid]::NewGuid().ToString('N').Substring(0, 8))"
$compose = @("-p", $ComposeProject, "--env-file", $EnvFile, "-f", "docker-compose.prod.yml")
$containerBackup = "/tmp/$restoreDb.dump"
$postgresContainer = (docker-compose @compose ps -q postgres).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($postgresContainer)) {
    throw "PostgreSQL container is not running."
}

try {
    docker cp ([IO.Path]::GetFullPath($BackupFile)) "${postgresContainer}:$containerBackup"
    if ($LASTEXITCODE -ne 0) { throw "Could not copy backup into PostgreSQL container." }
    docker-compose @compose exec -T postgres sh -c "createdb -U `$POSTGRES_USER $restoreDb"
    if ($LASTEXITCODE -ne 0) { throw "Could not create disposable restore database." }

    docker-compose @compose exec -T postgres sh -c "pg_restore -U `$POSTGRES_USER -d $restoreDb --no-owner --no-privileges $containerBackup"
    if ($LASTEXITCODE -ne 0) { throw "Restore failed." }

    $repositoryHead = (docker-compose @compose exec -T backend sh -c "alembic heads 2>/dev/null" | Select-String -Pattern '^[0-9a-f]+ \(head\)$').Line
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repositoryHead)) {
        throw "Could not determine the repository Alembic head."
    }
    $repositoryHead = ($repositoryHead -split ' ')[0]

    $restoredRevision = (docker-compose @compose exec -T postgres psql -U $dbUser -d $restoreDb -tAc "SELECT version_num FROM alembic_version").Trim()
    if ($LASTEXITCODE -ne 0 -or $restoredRevision -ne $repositoryHead) {
        throw "Restored Alembic revision does not match the repository head."
    }

    $schemaCheck = (docker-compose @compose exec -T postgres psql -U $dbUser -d $restoreDb -tAc "SELECT (to_regclass('public.users') IS NOT NULL AND to_regclass('public.knowledge_bases') IS NOT NULL)").Trim()
    if ($LASTEXITCODE -ne 0 -or $schemaCheck -ne "t") {
        throw "Required restored tables were not found."
    }

    $adminCheck = (docker-compose @compose exec -T postgres psql -U $dbUser -d $restoreDb -tAc "SELECT count(*) FROM users WHERE role='admin' AND is_active IS TRUE").Trim()
    if ($LASTEXITCODE -ne 0 -or [int]$adminCheck -lt 1) {
        throw "An active administrator was not found in the restored database."
    }

    $tables = @("users", "knowledge_bases", "documents", "document_chunks", "embedding_jobs", "embeddings")
    foreach ($table in $tables) {
        $productionCount = (docker-compose @compose exec -T postgres psql -U $dbUser -d $productionDb -tAc "SELECT count(*) FROM $table").Trim()
        if ($LASTEXITCODE -ne 0) { throw "Could not count production table $table." }
        $restoreCount = (docker-compose @compose exec -T postgres psql -U $dbUser -d $restoreDb -tAc "SELECT count(*) FROM $table").Trim()
        if ($LASTEXITCODE -ne 0) { throw "Could not count restored table $table." }
        if ($productionCount -ne $restoreCount) { throw "Row-count mismatch for $table." }
        Write-Host "Count match: $table = $productionCount"
    }

    Write-Host "Alembic revision matches repository head."
    Write-Host "Required tables and an active administrator are present."
    Write-Host "Restore drill passed using disposable database $restoreDb."
} finally {
    docker-compose @compose exec -T postgres sh -c "dropdb -U `$POSTGRES_USER --if-exists $restoreDb" | Out-Null
    docker exec -u 0 $postgresContainer rm -f $containerBackup | Out-Null
}
