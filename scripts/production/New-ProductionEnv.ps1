param(
    [string]$OutputFile = ".env.production",
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if ((Test-Path -LiteralPath $OutputFile) -and (Get-Item -LiteralPath $OutputFile).Length -gt 0 -and -not $Force) {
    throw "$OutputFile already contains data. Use -Force only when replacement is intentional."
}

function New-RandomHex([int]$ByteCount) {
    $bytes = [byte[]]::new($ByteCount)
    $generator = [Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    } finally {
        $generator.Dispose()
    }
    return ([BitConverter]::ToString($bytes) -replace "-", "").ToLowerInvariant()
}

$jwtSecret = New-RandomHex 48
$postgresPassword = New-RandomHex 32
$redisPassword = New-RandomHex 32

$content = @"
APP_ENV=production
FRONTEND_PORT=8081
HSTS_HEADER=
UVICORN_WORKERS=2

POSTGRES_DB=buyma_ai
POSTGRES_USER=buyma_user
POSTGRES_PASSWORD=$postgresPassword
DATABASE_URL=postgresql+asyncpg://buyma_user:$postgresPassword@postgres:5432/buyma_ai

REDIS_PASSWORD=$redisPassword
CELERY_BROKER_URL=redis://:$redisPassword@redis:6379/0
CELERY_RESULT_BACKEND=redis://:$redisPassword@redis:6379/1

SECRET_KEY=$jwtSecret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-5-mini

CORS_ALLOWED_ORIGINS=
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
REGISTRATION_ENABLED=false
ENABLE_API_DOCS=false

EMBEDDING_JOB_STALE_MINUTES=10
EMBEDDING_RECOVERY_BATCH_SIZE=100
"@

[IO.File]::WriteAllText([IO.Path]::GetFullPath($OutputFile), $content, [Text.UTF8Encoding]::new($false))

$jwtSecret = $null
$postgresPassword = $null
$redisPassword = $null
$content = $null

Write-Host "Production environment file created. Generated secret values were not printed."
Write-Host "Set a rotated production-only OPENAI_API_KEY before validation or startup."
