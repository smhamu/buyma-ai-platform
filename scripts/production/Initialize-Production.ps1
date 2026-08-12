param([string]$EnvFile = ".env.production")

$ErrorActionPreference = "Stop"
$compose = @("compose", "--env-file", $EnvFile, "-f", "docker-compose.prod.yml")

& "$PSScriptRoot\Test-ProductionEnv.ps1" -EnvFile $EnvFile
docker @compose config --quiet
if ($LASTEXITCODE -ne 0) { throw "Production Compose validation failed." }

docker @compose up -d postgres redis
if ($LASTEXITCODE -ne 0) { throw "Database services failed to start." }

docker @compose run --rm backend alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw "Alembic migration failed." }

docker @compose run --rm backend alembic current
if ($LASTEXITCODE -ne 0) { throw "Could not verify Alembic revision." }

Write-Host "Database initialized. Create the first administrator interactively:"
Write-Host "docker compose --env-file $EnvFile -f docker-compose.prod.yml run --rm backend python scripts/create_admin.py"
