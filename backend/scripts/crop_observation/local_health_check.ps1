param([string]$BaseUrl = "http://127.0.0.1:8015")
$ErrorActionPreference = "Stop"
Invoke-RestMethod "$BaseUrl/health/live" | ConvertTo-Json -Depth 6
Invoke-RestMethod "$BaseUrl/health/ready" | ConvertTo-Json -Depth 6
$openapi = Invoke-RestMethod "$BaseUrl/openapi.json"
Write-Host "Crop Observation routes: $($openapi.paths.PSObject.Properties.Count)"
Write-Host "Service health checks passed." -ForegroundColor Green
