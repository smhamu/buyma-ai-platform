param(
    [string]$BaseUrl = "http://localhost:8080",
    [string]$AdminEmail = $env:SMOKE_ADMIN_EMAIL,
    [string]$AdminPassword = $env:SMOKE_ADMIN_PASSWORD
)

$ErrorActionPreference = "Stop"
$base = $BaseUrl.TrimEnd('/')

foreach ($path in @("/", "/login", "/knowledge-bases", "/api/health")) {
    $statusCode = curl.exe --silent --show-error --output NUL --write-out "%{http_code}" "$base$path"
    if ($LASTEXITCODE -ne 0 -or $statusCode -ne "200") {
        throw "$path returned HTTP $statusCode."
    }
    Write-Host "PASS GET $path -> 200"
}

if ([string]::IsNullOrWhiteSpace($AdminEmail) -or [string]::IsNullOrWhiteSpace($AdminPassword)) {
    Write-Host "Authentication smoke test skipped. Set SMOKE_ADMIN_EMAIL and SMOKE_ADMIN_PASSWORD to enable it."
    exit 0
}

$loginBody = @{ email = $AdminEmail; password = $AdminPassword } | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$base/api/auth/login" -Method Post -ContentType "application/json" -Body $loginBody
$token = $login.data.access_token
if ([string]::IsNullOrWhiteSpace($token)) { throw "Login response did not contain an access token." }

$headers = @{ Authorization = "Bearer $token" }
$knowledgeBases = Invoke-RestMethod -Uri "$base/api/knowledge-bases" -Method Get -Headers $headers
if ($knowledgeBases.success -ne $true) { throw "Knowledge Base list request failed." }

Write-Host "PASS POST /api/auth/login"
Write-Host "PASS GET /api/knowledge-bases"
Write-Host "Smoke test completed. Credentials and tokens were not printed."
